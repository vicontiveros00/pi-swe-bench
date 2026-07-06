# pi-swe-bench

A small **agentic** bug-fixing benchmark for local coding models, driven by the
[Pi](https://pi.dev) harness. Each task is a tiny repo containing a buggy
`solution.py` and a failing test. Pi (running one of your LM Studio models as its
backend) is dropped into the workspace and has to **read, edit, and run** its way
to a fix. The task is graded by the state Pi leaves the repo in — run against a
**hidden** test set that is broader than the one the agent could see — not by
anything Pi says in its reply. Special-casing the visible example fails grading.

## Layout

```
pi-swe-bench/
├── .agents.md            # instructions Pi loads at startup (rules + how to verify)
├── config.py             # models under test + Pi invocation
├── run_bench.py          # orchestrator: drive Pi per task, grade, aggregate
├── analyze.ipynb         # dashboard: pass@1 tables, tier curves, run-over-run tracking
├── requirements-analysis.txt  # deps for the notebook only (runner needs none)
├── prompts.py            # task-prompt builder for the three guidance levels
├── grade.py              # run a test file against a workspace's solution.py
├── validate.py           # suite self-check (buggy fails, reference passes)
├── generate.py           # (re)materialize the tree from tasks.py
├── tasks.py              # source of truth: 14 tasks across 5 tiers
├── tasks/
│   ├── manifest.json     # id / dir / tier / entrypoint for the runner
│   └── NN_name/
│       ├── PROMPT.md         # task statement given to the agent
│       ├── solution.py       # buggy file (the ONLY file the agent edits)
│       └── test_public.py    # visible reproduction (the agent's target)
├── grading/NN_name/
│   └── test_hidden.py    # held-out grading tests (agent never sees these)
├── reference/NN_name/
│   └── solution.py       # known-good fix (used only by validate.py)
└── results/              # results.json + per-attempt diffs and logs
    ├── runs/<run_id>__<guidance>.json   # per-run archive: {meta, results}, never overwritten
    ├── results_<guidance>.json          # latest flat results at that guidance (convenience)
    └── artifacts/<guidance>/<model>/<task>/sample<k>/  # prompt.txt, solution.diff, pi.log, grade.log
```

## Prerequisites

- Pi installed and on `PATH`, already configured to see your LM Studio models
  (you have this).
- LM Studio's local server running with the target model loaded.
- `python` on `PATH` (stdlib only — no pip installs).

## Run

```bash
python validate.py                     # sanity-check the suite itself
python run_bench.py                    # all models, all tasks, standard prompt
python run_bench.py --tier 5           # only the hardest tier
python run_bench.py --model qwen3.5-9b # one model
python run_bench.py --samples 3        # stabler pass@1
python run_bench.py --guidance auto    # see below
```

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
per task. Every attempt also drops a `solution.diff`, `pi.log`, and `grade.log`
under `results/artifacts/<model>/<task>/` so you can see exactly what Pi changed.

### Model selection (read this before your first run)

Pi's `--model` is a **pattern matched against a model's `id`/`name`, not a
`provider/model` string**. If it matches nothing, Pi silently falls back to its
`defaultModel` and benchmarks the wrong model with no error. Pi also hides local
models behind auth: a keyless LM Studio provider stays *unavailable* to `--model`
unless the provider has a dummy `apiKey`, you've run `/login`, or you pass
`--api-key` (config exposes `PI_API_KEY` for this).

So, before running:

```bash
pi --list-models          # copy the EXACT gpt-oss / qwen ids into config.MODELS
```

Set each `pi_model` to that bare id (e.g. `gpt-oss-20b@f16`) — no `lmstudio/`
prefix. The runner does a **preflight** (`pi --list-models`) and aborts with a fix
recipe if an id isn't selectable, so a mismatch can't silently waste a run. Skip it
with `--no-check` once you trust the config. Sanity-check one task and watch which
model LM Studio loads:

```bash
python run_bench.py --tier 1 --model gpt-oss-20b
```

If LM Studio loads gemma (or anything unexpected), the id is wrong or unavailable —
fix `config.MODELS` / `PI_API_KEY`, don't scale up yet.

### Debugging a single task by hand

```bash
cd tasks/10_lru_cache
pi --model gpt-oss-20b@f16   # Pi loads .agents.md from the parent automatically
# ...let it work, then:
python test_public.py
```

## How grading avoids being gamed

The agent sees `test_public.py`, which contains only the single reproduction from
`PROMPT.md`. Scoring uses `grading/<task>/test_hidden.py`, a broader set covering
edge cases and boundaries. A model that "fixes" the bug by hard-coding the visible
input passes the public test but fails the hidden one. Imports resolve to the
agent's edited `solution.py` because the grader runs from inside the workspace.

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
`subprocess.Popen(["python", "run_bench.py", "--guidance", "standard"])`, then read
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

Edit `tasks.py` (copy a task dict; keep the shown example narrower than `check`),
then:

```bash
python generate.py     # rematerialize tasks/ grading/ reference/
python validate.py     # confirm buggy fails and reference passes, both tests
```
