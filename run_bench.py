#!/usr/bin/env python3
"""Drive Pi over the benchmark and score from repo state.

For each model x task x sample:
  1. copy the task workspace (solution.py, test_public.py, .agents.md) into an
     isolated temp dir and write a PROMPT.md at the chosen guidance level
  2. run Pi in print mode there, pointed at the model, with that prompt as the task
  3. grade the resulting solution.py against the HIDDEN test set
  4. record pass/fail, wall-clock time, and the diff Pi produced

The solution is judged by the state Pi leaves the repo in, not by anything it says
in its reply.

Each sample is classified pass / fail / errored. 'errored' means Pi made NO edit
AND produced no usable turn output (empty log or timeout) — a dropped/empty agent
turn or serving flake, not the model getting the bug wrong. Errored samples are
excluded from the pass@1 denominator and reported separately, so infrastructure
hiccups don't masquerade as capability failures. See classify_sample().

--guidance controls how much the agent is told (see prompts.py):
  auto     - symptom only; tests bug-finding as well as fixing
  standard - a bug report (default)
  guided   - names the buggy function; isolates fix ability from localization
Run the same models at two levels and compare: a big auto-vs-guided gap means the
weakness is diagnosis, not the fix.

Usage:
    python run_bench.py                        # all models, all tasks, standard
    python run_bench.py --guidance auto        # hardest level
    python run_bench.py --tier 5 --model qwen3.5-9b
    python run_bench.py --guidance guided --samples 3 --out results/guided.json
"""
import argparse
import datetime
import difflib
import json
import os
import platform
import shutil
import socket
import statistics
import subprocess
import tempfile
import time
import urllib.request
from collections import defaultdict

import config
from grade import run_test_file
from prompts import GUIDANCE_LEVELS, build_prompt

ROOT = os.path.dirname(os.path.abspath(__file__))
MANIFEST = json.load(open(os.path.join(ROOT, "tasks", "manifest.json")))
AGENTS_MD = os.path.join(ROOT, ".agents.md")


def git_info():
    """Return (short_sha, dirty_bool) so a run can be tied to repo state; (None, None) if not a git repo."""
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return None, None
    try:
        dirty = bool(subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip())
    except Exception:
        dirty = None
    return sha, dirty


def prepare_workspace(task):
    ws = tempfile.mkdtemp(prefix=f"pi-bench-{task['id']}-")
    src = os.path.join(ROOT, "tasks", task["dir"])
    # PROMPT.md is written per-run at the chosen guidance level, not copied.
    # Copy every source file the task ships (one file for tiers 1-5; a small repo
    # for tier 6) plus the public reproduction.
    for fn in list(task["files"]) + ["test_public.py"]:
        shutil.copy(os.path.join(src, fn), os.path.join(ws, fn))
    if os.path.exists(AGENTS_MD):
        # Ship it under the requested name AND the name Pi auto-discovers (AGENTS.md),
        # so the rules load regardless of whether your Pi picks up the dotfile.
        shutil.copy(AGENTS_MD, os.path.join(ws, ".agents.md"))
        shutil.copy(AGENTS_MD, os.path.join(ws, "AGENTS.md"))
    return ws


def pi_prefix():
    """Common leading args for any pi invocation (base flags + optional api key +
    the sampling extension if configured)."""
    key = getattr(config, "PI_API_KEY", None)
    ext = getattr(config, "SAMPLING_EXTENSION", None)
    args = [config.PI_BIN, *config.PI_BASE_ARGS]
    if key:
        args += ["--api-key", key]
    if ext and os.path.exists(ext):
        args += ["-e", ext]
    return args


def effective_sampling(temperature_override=None):
    """config.SAMPLING with an optional per-run temperature override applied."""
    samp = {k: v for k, v in getattr(config, "SAMPLING", {}).items()}
    if temperature_override is not None:
        samp["temperature"] = temperature_override
    return samp


def sampling_env(sampling):
    """Environment for a pi call: base env plus PI_SAMPLING_* read by sampling.js.
    Only non-None params are exported, so unset ones fall through to the server."""
    env = dict(os.environ)
    for k, v in sampling.items():
        if v is not None:
            env[f"PI_SAMPLING_{k.upper()}"] = str(v)
    return env


def lmstudio_loaded_ids(url, timeout=10):
    """Ask LM Studio which models are currently loaded. Returns a list of ids, or
    None if the endpoint can't be reached / doesn't support the query."""
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/api/v0/models", timeout=timeout) as r:
            data = json.loads(r.read())
    except Exception:
        return None
    loaded = []
    for m in data.get("data", []):
        state = str(m.get("state", "")).lower()
        if "loaded" in state and "not" not in state:  # "loaded" / "loaded-idle"
            loaded.append(m.get("id", ""))
    return loaded


def model_token(pi_model):
    """Distinctive part of an id for matching against LM Studio's loaded id:
    drop the provider prefix and any @quant suffix. 'lmstudio/gpt-oss-20b@f16' -> 'gpt-oss-20b'."""
    return pi_model.split("/")[-1].split("@")[0].lower()


def preflight(models):
    """Probe each model with a tiny prompt to confirm Pi can actually SELECT and
    REACH it, then (if config.LMSTUDIO_URL is set) confirm LM Studio loaded the
    model we asked for rather than silently falling back to its default.
    """
    probe = "Reply with the single word READY and nothing else."
    env = sampling_env(effective_sampling())
    url = getattr(config, "LMSTUDIO_URL", None)
    ok_all = True
    for m in models:
        cmd = pi_prefix() + [*config.PI_MODEL_ARGS, m["pi_model"], probe]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=getattr(config, "PREFLIGHT_TIMEOUT", 240),
                               env=env)
        except FileNotFoundError:
            raise SystemExit(f"Could not run '{config.PI_BIN}'. Is Pi installed and on PATH?")
        except subprocess.TimeoutExpired:
            print(f"  preflight {m['name']:<12} {m['pi_model']:<28} slow (model load?) — assuming ok")
            continue
        out = (r.stdout + r.stderr).strip()
        bad = (r.returncode != 0
               or not out
               or any(s in out for s in ("No API key", "API key", "401", "Invalid", "not found")))
        reason = "" if not bad else f"pi said: {out.splitlines()[-1] if out else '(no output)'}"

        # Cross-check: did LM Studio load what we asked for, or fall back?
        if not bad and url:
            loaded = lmstudio_loaded_ids(url)
            if loaded is not None:
                token = model_token(m["pi_model"])
                if not any(token in x.lower() for x in loaded):
                    bad = True
                    reason = (f"asked for {m['pi_model']} but LM Studio loaded {loaded or '[none]'} "
                              "— Pi fell back to a different model")

        print(f"  preflight {m['name']:<12} {m['pi_model']:<28} {'FAILED' if bad else 'ok'}")
        if bad:
            ok_all = False
            print(f"      {reason}")
    if not ok_all:
        print("\nA model could not be selected/reached (or Pi fell back). Fixes:")
        print("  - Run `pi --list-models` and copy the EXACT gpt-oss id (the @quant tag or")
        print("    the model may differ from what's in config.MODELS, or it isn't downloaded).")
        print("  - Keep the provider prefix, e.g. 'lmstudio/<id>'.")
        print("  - Keyless LM Studio needs auth: config.PI_API_KEY (e.g. 'lmstudio') or `/login`.")
        print("  - Re-run, or pass --no-check to skip this probe.")
    return ok_all


def run_pi(pi_model, prompt, ws, sampling):
    cmd = pi_prefix() + [*config.PI_MODEL_ARGS, pi_model, prompt]
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd, cwd=ws, capture_output=True, text=True, timeout=config.PI_TIMEOUT,
            env=sampling_env(sampling),
        )
        log = proc.stdout + proc.stderr
        err = None
    except subprocess.TimeoutExpired:
        log, err = "PI_TIMEOUT", "timeout"
    except FileNotFoundError:
        raise SystemExit(
            f"Could not run '{config.PI_BIN}'. Is Pi installed and on PATH? "
            "See config.py to adjust PI_BIN / PI_MODEL_ARGS."
        )
    return time.time() - t0, log, err


def unified_diff(before, after, fn):
    return "".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile=f"{fn} (before)", tofile=f"{fn} (after)",
    ))


def classify_sample(ok, made_edit, log, err):
    """Distinguish a real capability failure from a harness/serving flake.

    A sample is 'errored' (not 'fail') when Pi effectively did nothing: it made
    NO edit to any source file AND produced no usable turn output (empty log or a
    hard timeout). That pattern means a dropped/empty agent turn, not the model
    getting the bug wrong, so it should not count against pass@1. Anything that
    edited a file (right or wrong) or produced a real transcript is judged on the
    hidden test as before.
    """
    if ok:
        return "pass"
    stripped = (log or "").strip()
    no_output = err == "timeout" or not stripped or stripped == "PI_TIMEOUT"
    if not made_edit and no_output:
        return "errored"
    return "fail"


def pass_at_k(n, c, k):
    """Unbiased pass@k estimate (Chen et al. 2021): probability that at least one
    of k samples drawn from n scored attempts passes, given c of them passed.
    Returns None if k > n (can't estimate).  Errored samples are excluded upstream,
    so n here is the number of samples that actually ran."""
    if k > n or n == 0:
        return None
    if c == 0:
        return 0.0
    if n - c < k:
        return 1.0  # fewer than k failures -> every draw of k contains a pass
    # 1 - C(n-c, k)/C(n, k), computed stably as a product
    prob_all_fail = 1.0
    for i in range(k):
        prob_all_fail *= (n - c - i) / (n - i)
    return 1.0 - prob_all_fail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", type=int, default=None)
    ap.add_argument("--model", default=None, help="run only this model name")
    ap.add_argument("--samples", type=int, default=config.SAMPLES)
    ap.add_argument("--temperature", type=float, default=None,
                    help="override config.SAMPLING temperature for this run "
                         "(e.g. 0.0 for a deterministic capability run). Run at "
                         "several temps to sweep the sampling-vs-reliability curve.")
    ap.add_argument("--guidance", choices=GUIDANCE_LEVELS, default="standard",
                    help="how much the agent is told (auto|standard|guided)")
    ap.add_argument("--out", default=None,
                    help="results json path (default: results/results_<guidance>.json)")
    ap.add_argument("--no-check", action="store_true",
                    help="skip the pre-run model preflight (pi --list-models)")
    args = ap.parse_args()

    tasks = [t for t in MANIFEST if args.tier is None or t["tier"] == args.tier]
    models = [m for m in config.MODELS if args.model is None or m["name"] == args.model]

    if not args.no_check:
        print("preflight: probing each model (a tiny prompt; may load the model)...")
        if not preflight(models):
            raise SystemExit(1)
    # keep guidance runs in separate artifact trees so they don't clobber each other
    artifacts_root = os.path.join(ROOT, "results", "artifacts", args.guidance)

    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    sha, dirty = git_info()
    meta = {
        "run_id": run_id,
        "timestamp": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "guidance": args.guidance,
        "samples": args.samples,
        "tier_filter": args.tier,
        "models": [{"name": m["name"], "pi_model": m["pi_model"]} for m in models],
        "git_sha": sha,
        "git_dirty": dirty,
        "pi_base_args": config.PI_BASE_ARGS,
        "pi_model_args": config.PI_MODEL_ARGS,
        "pi_timeout": config.PI_TIMEOUT,
        "sampling": {k: v for k, v in effective_sampling(args.temperature).items() if v is not None},
        "sampling_extension": bool(getattr(config, "SAMPLING_EXTENSION", None)
                                   and os.path.exists(getattr(config, "SAMPLING_EXTENSION", ""))),
        "host": socket.gethostname(),
        "python": platform.python_version(),
    }
    dirty_note = " (dirty)" if dirty else ""
    print(f"run_id {run_id}  |  git {sha or 'n/a'}{dirty_note}  |  "
          f"guidance {args.guidance}  |  samples {args.samples}")
    samp = meta["sampling"]
    if samp:
        via = "extension" if meta["sampling_extension"] else "NOT APPLIED (sampling.js missing)"
        override = "  [--temperature override]" if args.temperature is not None else ""
        print("  sampling: " + ", ".join(f"{k}={v}" for k, v in samp.items()) + f"  (via {via}){override}")
    else:
        print("  sampling: provider/LM Studio defaults (none overridden)")

    results = []
    for model in models:
        print(f"\n=== {model['name']}  ({model['pi_model']})  [guidance: {args.guidance}] ===")
        for task in tasks:
            passes, errored, times = 0, 0, []
            for s in range(args.samples):
                ws = prepare_workspace(task)
                before = {fn: open(os.path.join(ws, fn)).read() for fn in task["files"]}
                prompt = build_prompt(args.guidance, task["title"],
                                      task["spec"], task["entrypoint"],
                                      editable=task.get("editable", task["files"]))
                with open(os.path.join(ws, "PROMPT.md"), "w") as f:
                    f.write(prompt)

                dt, log, err = run_pi(model["pi_model"], prompt, ws,
                                      effective_sampling(args.temperature))
                times.append(dt)

                hidden = os.path.join(ROOT, "grading", task["dir"], "test_hidden.py")
                ok, grade_log = run_test_file(ws, hidden, config.GRADE_TIMEOUT)

                # One diff per shipped file (concatenated); tier-6 edits may span files.
                diff_all = ""
                for fn in task["files"]:
                    after = open(os.path.join(ws, fn)).read()
                    diff_all += unified_diff(before[fn], after, fn)
                made_edit = bool(diff_all.strip())

                status = classify_sample(ok, made_edit, log, err)
                if status == "pass":
                    passes += 1
                elif status == "errored":
                    errored += 1

                # save artifacts for inspection
                adir = os.path.join(artifacts_root, model["name"], task["dir"], f"sample{s}")
                os.makedirs(adir, exist_ok=True)
                with open(os.path.join(adir, "prompt.txt"), "w") as f:
                    f.write(prompt)
                with open(os.path.join(adir, "solution.diff"), "w") as f:
                    f.write(diff_all or "(no change)\n")
                with open(os.path.join(adir, "pi.log"), "w") as f:
                    f.write(log or "")
                with open(os.path.join(adir, "grade.log"), "w") as f:
                    f.write(grade_log or "")
                with open(os.path.join(adir, "status.txt"), "w") as f:
                    f.write(status + "\n")
                shutil.rmtree(ws, ignore_errors=True)

            n = args.samples
            scored = n - errored  # samples that actually ran; pass@k denominator
            # pass@k for the k's that fit in this run (1,2,5,10,... up to scored)
            k_values = [k for k in (1, 2, 3, 5, 10) if k <= scored]
            patk = {k: pass_at_k(scored, passes, k) for k in k_values}
            if scored == 0:
                mark = "ER "
            else:
                mark = "OK " if passes == scored else ("~  " if passes else "XX ")
            err_note = f"  (+{errored} errored)" if errored else ""
            # show pass@k spread only when we have more than one scored sample
            pk_note = ""
            if scored > 1 and patk:
                lo, hi = min(k_values), max(k_values)
                pk_note = f"  [pass@{lo}={patk[lo]:.0%} pass@{hi}={patk[hi]:.0%}]"
            print(f"  [{mark}] T{task['tier']} {task['dir']:<22} {passes}/{scored}{err_note}{pk_note}  "
                  f"({statistics.mean(times):.0f}s avg)")
            results.append({
                "run_id": run_id, "timestamp": meta["timestamp"], "git_sha": sha,
                "model": model["name"], "task": task["id"], "tier": task["tier"],
                "guidance": args.guidance,
                "passes": passes, "n": n, "errored": errored, "scored": scored,
                "pass_at_1": (passes / scored) if scored else None,
                "pass_at_k": {str(k): v for k, v in patk.items()},
                "resolved": passes > 0,
                "avg_seconds": statistics.mean(times) if times else None,
            })

    summarize(results, args.guidance, meta["sampling"])

    # Per-run archive: the experiment log the notebook reads. Never overwritten.
    runs_dir = os.path.join(ROOT, "results", "runs")
    os.makedirs(runs_dir, exist_ok=True)
    archive = os.path.join(runs_dir, f"{run_id}__{args.guidance}.json")
    json.dump({"meta": meta, "results": results}, open(archive, "w"), indent=2)

    # Convenience: latest flat results at this guidance (honours --out if given).
    out_rel = args.out or f"results/results_{args.guidance}.json"
    out = os.path.join(ROOT, out_rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(results, open(out, "w"), indent=2)

    print(f"\nSaved run archive results/runs/{run_id}__{args.guidance}.json")
    print(f"Saved latest      {out_rel}   "
          f"(prompts, diffs & logs under results/artifacts/{args.guidance}/)")


def summarize(results, guidance="standard", sampling=None):
    print("\n" + "=" * 56)
    print(f"guidance: {guidance}")
    if sampling:
        print("sampling: " + ", ".join(f"{k}={v}" for k, v in sampling.items()))
    by_model = defaultdict(list)
    for r in results:
        by_model[r["model"]].append(r)
    for model, rs in by_model.items():
        n = len(rs)
        scored = [r for r in rs if r["pass_at_1"] is not None]
        p1 = statistics.mean(r["pass_at_1"] for r in scored) if scored else float("nan")
        resolved = sum(r["resolved"] for r in rs)
        total_errored = sum(r.get("errored", 0) for r in rs)
        total_samples = sum(r.get("n", 0) for r in rs)
        tiers = defaultdict(list)
        for r in scored:
            tiers[r["tier"]].append(r["pass_at_1"])
        secs = [r["avg_seconds"] for r in rs if r["avg_seconds"]]
        # Aggregate pass@k across tasks: mean of per-task pass@k, only for k's that
        # every scored task supports (so the average is over the same task set).
        k_sets = [set(int(k) for k in r.get("pass_at_k", {})) for r in scored]
        common_k = sorted(set.intersection(*k_sets)) if k_sets and all(k_sets) else []
        agg_patk = {}
        for k in common_k:
            vals = [r["pass_at_k"][str(k)] for r in scored if r["pass_at_k"].get(str(k)) is not None]
            if vals:
                agg_patk[k] = statistics.mean(vals)
        print(f"\n{model}")
        print(f"  overall pass@1 : {p1:6.1%}" + ("  (errored samples excluded)" if total_errored else ""))
        # Only show the pass@k curve when there's more than one sample per task.
        curve_ks = [k for k in common_k if k > 1]
        if curve_ks:
            curve = "  ".join(f"pass@{k}={agg_patk[k]:.1%}" for k in curve_ks)
            print(f"  reliability    : {curve}")
            gap = agg_patk[curve_ks[-1]] - p1
            if gap > 0.05:
                print(f"  ↳ pass@{curve_ks[-1]} beats pass@1 by {gap:+.1%}: the model often "
                      "KNOWS the fix but samples it inconsistently (lower temperature).")
        print(f"  resolved (>=1) : {resolved}/{n}")
        if total_errored:
            print(f"  errored        : {total_errored}/{total_samples} samples "
                  f"(no edit + no output; harness/serving flake, not counted)")
        for t in sorted(tiers):
            print(f"  tier {t} pass@1 : {statistics.mean(tiers[t]):6.1%}  (n={len(tiers[t])})")
        if secs:
            print(f"  avg wall time  : {statistics.mean(secs):6.0f}s/task")


if __name__ == "__main__":
    main()