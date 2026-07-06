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
    for fn in ("solution.py", "test_public.py"):
        shutil.copy(os.path.join(src, fn), os.path.join(ws, fn))
    if os.path.exists(AGENTS_MD):
        # Ship it under the requested name AND the name Pi auto-discovers (AGENTS.md),
        # so the rules load regardless of whether your Pi picks up the dotfile.
        shutil.copy(AGENTS_MD, os.path.join(ws, ".agents.md"))
        shutil.copy(AGENTS_MD, os.path.join(ws, "AGENTS.md"))
    return ws


def pi_prefix():
    """Common leading args for any pi invocation (base flags + optional api key)."""
    key = getattr(config, "PI_API_KEY", None)
    return [config.PI_BIN, *config.PI_BASE_ARGS] + (["--api-key", key] if key else [])


def preflight(models):
    """Verify each configured model is actually selectable before running.

    Pi silently falls back to its defaultModel when --model matches nothing, so a
    wrong id means you benchmark the wrong model (e.g. gemma) without any error.
    We run `pi --list-models` and check each pi_model id appears in the output.
    Returns True if all present; prints guidance and returns False otherwise.
    """
    key = getattr(config, "PI_API_KEY", None)
    cmd = [config.PI_BIN, "--list-models"] + (["--api-key", key] if key else [])
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        raise SystemExit(f"Could not run '{config.PI_BIN}'. Is Pi installed and on PATH?")
    except subprocess.TimeoutExpired:
        print("preflight: `pi --list-models` timed out; skipping check.")
        return True
    listing = out.stdout + out.stderr
    missing = [m for m in models if m["pi_model"] not in listing]
    for m in models:
        status = "missing/unavailable" if m in missing else "ok"
        print(f"  preflight {m['name']:<12} {m['pi_model']:<24} {status}")
    if missing:
        print("\nThese model ids are not selectable via `pi --list-models`.")
        print("Fix before running, or Pi will fall back to its default model:")
        print("  1. Run `pi --list-models` and copy the EXACT id into config.MODELS.")
        print("  2. If the id is listed but unavailable, it's auth: give the lmstudio")
        print("     provider a dummy apiKey in ~/.pi/agent/models.json, or set")
        print("     config.PI_API_KEY (currently "
              f"{getattr(config, 'PI_API_KEY', None)!r}).")
        print("  3. Re-run, or pass --no-check to skip this guard.")
    return not missing


def run_pi(pi_model, prompt, ws):
    cmd = pi_prefix() + [*config.PI_MODEL_ARGS, pi_model, prompt]
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd, cwd=ws, capture_output=True, text=True, timeout=config.PI_TIMEOUT
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


def unified_diff(before, after):
    return "".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile="solution.py (before)", tofile="solution.py (after)",
    ))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", type=int, default=None)
    ap.add_argument("--model", default=None, help="run only this model name")
    ap.add_argument("--samples", type=int, default=config.SAMPLES)
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
        print("preflight: checking models resolve via `pi --list-models`...")
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
        "host": socket.gethostname(),
        "python": platform.python_version(),
    }
    dirty_note = " (dirty)" if dirty else ""
    print(f"run_id {run_id}  |  git {sha or 'n/a'}{dirty_note}  |  "
          f"guidance {args.guidance}  |  samples {args.samples}")

    results = []
    for model in models:
        print(f"\n=== {model['name']}  ({model['pi_model']})  [guidance: {args.guidance}] ===")
        for task in tasks:
            passes, times = 0, []
            for s in range(args.samples):
                ws = prepare_workspace(task)
                before = open(os.path.join(ws, "solution.py")).read()
                prompt = build_prompt(args.guidance, task["title"],
                                      task["spec"], task["entrypoint"])
                with open(os.path.join(ws, "PROMPT.md"), "w") as f:
                    f.write(prompt)

                dt, log, err = run_pi(model["pi_model"], prompt, ws)
                times.append(dt)

                hidden = os.path.join(ROOT, "grading", task["dir"], "test_hidden.py")
                ok, grade_log = run_test_file(ws, hidden, config.GRADE_TIMEOUT)
                passes += int(ok)

                # save artifacts for inspection
                adir = os.path.join(artifacts_root, model["name"], task["dir"], f"sample{s}")
                os.makedirs(adir, exist_ok=True)
                after = open(os.path.join(ws, "solution.py")).read()
                with open(os.path.join(adir, "prompt.txt"), "w") as f:
                    f.write(prompt)
                with open(os.path.join(adir, "solution.diff"), "w") as f:
                    f.write(unified_diff(before, after) or "(no change)\n")
                with open(os.path.join(adir, "pi.log"), "w") as f:
                    f.write(log or "")
                with open(os.path.join(adir, "grade.log"), "w") as f:
                    f.write(grade_log or "")
                shutil.rmtree(ws, ignore_errors=True)

            n = args.samples
            mark = "OK " if passes == n else ("~  " if passes else "XX ")
            print(f"  [{mark}] T{task['tier']} {task['dir']:<22} {passes}/{n}  "
                  f"({statistics.mean(times):.0f}s avg)")
            results.append({
                "run_id": run_id, "timestamp": meta["timestamp"], "git_sha": sha,
                "model": model["name"], "task": task["id"], "tier": task["tier"],
                "guidance": args.guidance,
                "passes": passes, "n": n, "pass_at_1": passes / n,
                "resolved": passes > 0,
                "avg_seconds": statistics.mean(times) if times else None,
            })

    summarize(results, args.guidance)

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


def summarize(results, guidance="standard"):
    print("\n" + "=" * 56)
    print(f"guidance: {guidance}")
    by_model = defaultdict(list)
    for r in results:
        by_model[r["model"]].append(r)
    for model, rs in by_model.items():
        n = len(rs)
        p1 = statistics.mean(r["pass_at_1"] for r in rs)
        resolved = sum(r["resolved"] for r in rs)
        tiers = defaultdict(list)
        for r in rs:
            tiers[r["tier"]].append(r["pass_at_1"])
        secs = [r["avg_seconds"] for r in rs if r["avg_seconds"]]
        print(f"\n{model}")
        print(f"  overall pass@1 : {p1:6.1%}")
        print(f"  resolved (>=1) : {resolved}/{n}")
        for t in sorted(tiers):
            print(f"  tier {t} pass@1 : {statistics.mean(tiers[t]):6.1%}  (n={len(tiers[t])})")
        if secs:
            print(f"  avg wall time  : {statistics.mean(secs):6.0f}s/task")


if __name__ == "__main__":
    main()
