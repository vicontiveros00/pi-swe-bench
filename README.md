# pi-swe-bench

A small **agentic** bug-fixing benchmark for local coding models, driven by the
[Pi](https://pi.dev) harness. Each task is a tiny repo containing buggy code and a
failing test. Pi (running one of your LM Studio models as its backend) is dropped
into the workspace and has to **read, edit, and run** its way to a fix. The task is
graded by the state Pi leaves the repo in — run against a **hidden** test set that
is broader than the one the agent could see — not by anything Pi says in its
reply. Special-casing the visible example fails grading.

Tasks span six tiers:

- **Tiers 1–5 — single-file, single-function bugs** (surface → algorithmic). One
  `solution.py` per task; the bug and its fix live in the same function.
- **Tier 6 — the multi-file tie-breaker.** Small repos where the *symptom* the
  public test shows lives in a **different file** from its *cause*. The tempting
  one-line patch at the symptom site passes the public test but fails the wider
  hidden set, so only a fix at the true cause scores. These reward real
  bug-finding and cross-file navigation — run them at `--guidance auto` to
  separate models that saturate the easy tiers.

Current tier 6 tasks: `15_cart_totals` (rounding bug in `pricing.py` surfacing in
`cart.py`), `16_event_bus` (`Registry.remove` mismatch in `registry.py`),
`17_paginate` (`page_count` off-by-one in `page_math.py`).

## Layout

```
pi-swe-bench/
├── .agents.md            # instructions Pi loads at startup (rules + how to verify)
├── config.py             # models under test + Pi invocation + SAMPLING params
├── sampling.js           # Pi extension: applies temperature/top_p/etc per request
├── run_bench.py          # orchestrator: drive Pi per task, grade, aggregate
├── analyze.ipynb         # dashboard: pass@1 tables, tier curves, run-over-run tracking
├── requirements-analysis.txt  # deps for the notebook only (runner needs none)
├── prompts.py            # task-prompt builder for the three guidance levels
├── grade.py              # run a test file against a workspace's solution.py
├── validate.py           # suite self-check (buggy fails, reference passes)
├── generate.py           # (re)materialize the tree from tasks.py
├── tasks.py              # source of truth: tasks across 6 tiers (tier 6 = multi-file)
├── tasks/
│   ├── manifest.json     # id / dir / tier / entrypoint / entry_module / files / editable
│   └── NN_name/
│       ├── PROMPT.md         # task statement given to the agent
│       ├── <module>.py       # buggy file(s): solution.py, or a small repo for tier 6
│       └── test_public.py    # visible reproduction (the agent's target)
├── grading/NN_name/
│   └── test_hidden.py    # held-out grading tests (agent never sees these)
├── reference/NN_name/
│   └── <module>.py       # known-good fix(es) (used only by validate.py)
└── results/              # results.json + per-attempt diffs and logs
    ├── runs/<run_id>__<guidance>.json   # per-run archive: {meta, results}, never overwritten
    ├── results_<guidance>.json          # latest flat results at that guidance (convenience)
    └── artifacts/<guidance>/<model>/<task>/sample<k>/  # prompt.txt, solution.diff, pi.log, grade.log
```

## Prerequisites

- Pi installed and on `PATH`, already configured to see your LM Studio models
  (you have this).
- LM Studio's local server running with the target model loaded.
- `python3` on `PATH` (stdlib only — no pip installs). This machine has only
  `python3`, so all commands below use it.
- `node` on `PATH` (ships with Pi) so `sampling.js` can load — only needed if you
  keep the `SAMPLING` overrides enabled.

## Run

```bash
python3 validate.py                     # sanity-check the suite itself
python3 run_bench.py                    # all models, all tasks, standard prompt
python3 run_bench.py --tier 5           # only the hardest single-file tier
python3 run_bench.py --tier 6 --guidance auto   # the multi-file tie-breaker
python3 run_bench.py --model gpt-oss-20b # one model (name from config.MODELS)
python3 run_bench.py --samples 10       # 10 attempts/task -> stable pass@1 + pass@k curve
python3 run_bench.py --temperature 0.0  # deterministic "capability" run (best for tie-breaks)
python3 run_bench.py --guidance auto    # see below
```

### Adjusting temperature & other sampling params

Pi has **no CLI flag** for sampling params (temperature, top_p, top_k, min_p,
penalties) — its only sampling-adjacent flag is `--thinking`. So the benchmark
sets them two supported ways:

1. **`config.py` → `SAMPLING` dict + `sampling.js` (recommended).** The extension
   `sampling.js` is loaded automatically (via `-e`) and stamps the params onto
   every provider request using Pi's `before_provider_request` hook. Edit the
   dict to change any value; set one to `None` to leave it at the LM Studio
   server-side default. The defaults mirror a real agentic setup:

   ```python
   SAMPLING = {
       "temperature": 0.6, "top_p": 0.95, "top_k": 20,
       "min_p": 0.05, "presence_penalty": 1.5, "repeat_penalty": 1.0,
   }
   ```

   Every run **prints and archives** the exact params used (in the header and in
   each run's `meta`), so results stay reproducible. Set
   `SAMPLING_EXTENSION = None` to disable the extension entirely and fall back to
   LM Studio's server-side sliders.

2. **`--temperature <float>` flag** overrides just the temperature for one run,
   without editing config — ideal for a sweep (`--temperature 0.0`, then `0.3`,
   then `0.6`). Other params keep their `SAMPLING` values, and the header tags
   the run with `[--temperature override]`.

> **Note on param support.** `temperature`, `top_p`, and `presence_penalty` are
> standard OpenAI-style keys and always apply. `top_k`, `min_p`, and
> `repeat_penalty` are llama.cpp-style; LM Studio's OpenAI-compatible endpoint
> accepts them, but if any is ignored, set it in LM Studio's server-side sampling
> panel instead and leave it `None` here.

> **Extensions gotcha.** `sampling.js` must **default-export a function** that
> receives `pi` (`export default function (pi) { pi.on(...) }`) — a bare global
> `pi` fails to load. If a *user* extension in `~/.pi/agent/extensions/` crashes
> in print mode (e.g. a footer/TUI extension), it can abort the run; disable it by
> moving it out of that directory.

#### Temperature answers two different questions — run it twice

- **Capability / tie-break — `--temperature 0.0`.** Deterministic: each model shows
  its single most-likely behaviour, so a real difference is visible and
  reproducible. Use this as the headline number, especially for tier 6.
- **Real-world fidelity — your production temp (e.g. 0.6) with `--samples 10`.**
  Captures sampling noise the way you actually run the model, reported as a
  **pass@k** reliability curve. A big `pass@k` – `pass@1` gap means the model
  *knows* the fix but samples it inconsistently — a concrete reason to lower
  temperature for agentic work.

`pass@k` uses the unbiased Chen et al. (2021) estimator over the samples that
actually **ran** (errored samples are excluded — see "Output" below).

### Guidance levels (`--guidance`)

How much the agent is told, so you can separate *finding* the bug from *fixing* it
(prompt text lives in `prompts.py`):

- `auto` — symptom only ("the tests are failing, fix it"). Hardest; tests diagnosis.
- `standard` — a bug report (default; matches the materialized `PROMPT.md`).
- `guided` — names the buggy function/class. Isolates fix ability from localization.

Run the same models at two levels and compare. A big `auto`-vs-`guided` gap means
the weakness is diagnosis, not the fix — the more interesting result for an agent,
and invisible in a single number. Each level writes its own
`results/results_<level>.json` and `results/artifacts/<level>/...` (including the
exact `prompt.txt` used), so levels never clobber each other.

The reasoning regime (gpt-oss effort / Qwen thinking) stays a model-level setting
in your Pi/LM Studio config — keep it matched and out of these prompts.

Output is per-tier and overall `pass@1`, resolve rate, and average wall-clock time
per task. With `--samples > 1` each task also reports a **pass@k reliability
curve** and every attempt is classified `pass` / `fail` / `errored`; **errored**
samples (agent made no edit *and* produced no output/timed out — a harness or
serving flake) are excluded from the pass@1/pass@k denominator rather than counted
as failures. Every attempt drops a `solution.diff`, `pi.log`, `grade.log`, and
`status.txt` under `results/artifacts/<guidance>/<model>/<task>/sample<k>/` so you
can see exactly what Pi changed.

### Model selection (read this before your first run)

Pi selects a model with `--model <provider/model>`. For LM Studio you need **both**
the provider prefix on the id **and** auth for the (keyless) provider. If `--model`
matches nothing, Pi silently falls back to its `defaultModel` and benchmarks the
wrong model with no error, so `config.py` sets:

- `pi_model` = the provider-prefixed id, e.g. `lmstudio/gpt-oss-20b` (keep the
  `lmstudio/` prefix).
- `PI_API_KEY = "lmstudio"` so the keyless LM Studio provider is selectable (or run
  `/login` for that provider instead).

Before running, get the exact ids:

```bash
pi --list-models          # copy the EXACT gpt-oss / gemma ids into config.MODELS
```

The runner does a **preflight** that probes each model and (if `config.LMSTUDIO_URL`
is set) asks LM Studio which model actually loaded, aborting with a fix recipe if an
id isn't selectable or Pi fell back — so a mismatch can't silently waste a run. Skip
it with `--no-check` once you trust the config. Sanity-check one task and watch which
model LM Studio loads:

```bash
python3 run_bench.py --tier 1 --model gpt-oss-20b
```

If LM Studio loads gemma (or anything unexpected), the id is wrong or unavailable —
fix `config.MODELS` / `PI_API_KEY`, don't scale up yet.

### Debugging a single task by hand

```bash
cd tasks/10_lru_cache
pi --model lmstudio/gpt-oss-20b   # Pi loads .agents.md from the parent automatically
# ...let it work, then:
python3 test_public.py
```

## How grading avoids being gamed

The agent sees `test_public.py`, which contains only the single reproduction from
`PROMPT.md`. Scoring uses `grading/<task>/test_hidden.py`, a broader set covering
edge cases and boundaries. A model that "fixes" the bug by hard-coding the visible
input passes the public test but fails the hidden one. For **tier 6** the same
mechanism punishes symptom-only patches: the visible fix site (e.g. bumping a page
count by one, or special-casing a total) satisfies the public test but breaks the
hidden boundary cases, so only a fix at the true cause — often in a different file
— scores. Imports resolve to the agent's edited files because the grader runs from
inside the workspace, which retains every module the task ships.

## Adding a multi-file (tier 6) task

Single-file tasks use `buggy`/`reference` strings. A multi-file task instead gives
the whole starter repo and its fixed form:

```python
{
  "name": "cart_totals", "tier": 6, "title": "...",
  "entrypoint": "Cart",           # public symbol the grader relies on
  "entry_module": "cart",         # module the tests `import` (default "solution")
  "editable": ["cart.py", "pricing.py"],   # files the agent may edit (named in PROMPT.md)
  "files": {"cart.py": "...", "pricing.py": "..."},          # buggy repo
  "reference_files": {"cart.py": "...", "pricing.py": "..."}, # fixed repo (validate.py only)
  "spec": "...", "check": "import cart as C\n...",           # hidden checks import the module themselves
}
```

The hidden `check` (and the `PUBLIC` reproduction in `generate.py`) must
`import <entry_module>` themselves rather than using `mod.` — the generator only
rewrites `mod.`→`solution.` for single-file tasks. Design the bug so the *symptom*
and *cause* sit in different files and the obvious local patch fails a hidden
boundary case. Then `python3 generate.py && python3 validate.py`.

## Tracking & analysis (`analyze.ipynb`)

Each run writes a stamped archive to `results/runs/<run_id>__<guidance>.json`
containing the full `meta` (timestamp, git SHA + dirty flag, guidance, samples,
model ids, Pi args, host) and every result row. Archives are never overwritten, so
they accumulate into an experiment log.

`analyze.ipynb` reads all of them into one DataFrame and gives you pass@1 by
model × tier, the auto-vs-guided diagnosis gap, run-over-run trend + delta, a
latency/pass scatter, and a failure list with artifact paths. It only reads JSON —
nothing launches a model — so it's fast and safe to re-run.

```bash
pip install -r requirements-analysis.txt   # pandas, matplotlib, jupyterlab
jupyter lab analyze.ipynb                   # run all cells after a benchmark run
```

Keep the runner as the engine and the notebook as the dashboard: don't move the
long Pi loop into a cell (a 20–30 min blocking cell that dies with the kernel is
fragile). To launch from the notebook without blocking, shell out:
`subprocess.Popen(["python3", "run_bench.py", "--guidance", "standard"])`, then read
the JSON once it finishes.



The harness controls the task and grading; a few confounds live in your Pi/LM
Studio setup:

- **Reasoning parity.** gpt-oss always emits CoT; keep its reasoning effort and
  Qwen's thinking mode matched (set in your Pi model definition / LM Studio), or
  you're measuring test-time compute rather than the model.
- **Same load params.** Match context length, KV-cache quant, and full GPU offload
  across both models (on your M4 Pro they both fit fully).
- **Agent budget.** `PI_TIMEOUT` and the model's max turns cap how long each attempt
  runs; keep them equal across models. A model that "fails" may have just run out of
  turns — check `pi.log`.

## Extending

Edit `tasks.py` (copy a task dict; keep the shown example narrower than `check`).
For a multi-file tier-6 task, use the `files`/`reference_files`/`entry_module`
shape instead — see "Adding a multi-file (tier 6) task" above. Then:

```bash
python3 generate.py     # rematerialize tasks/ grading/ reference/
python3 validate.py     # confirm buggy fails and reference passes, both tests
```
