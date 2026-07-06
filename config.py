"""Benchmark configuration.

IMPORTANT — model selection (this is what bit the first run):
Pi's `--model` takes a PATTERN matched against a model's `id`/`name`, NOT a
`provider/model` string. Passing something that matches nothing makes Pi fall
back to its `defaultModel` (e.g. gemma) and silently benchmark the wrong model.

So `pi_model` below must be the model id exactly as `pi --list-models` prints it
(the LM Studio API identifier, e.g. `gpt-oss-20b@f16`) — no `lmstudio/` prefix.

Pi also hides local models behind auth: a keyless LM Studio provider stays
"unavailable" for `--model` unless the provider has a dummy apiKey, you've run
`/login`, or you pass `--api-key`. PI_API_KEY below covers that last option.
Verify everything with:  pi --list-models
"""

# --- Pi invocation --------------------------------------------------------
PI_BIN = "pi"

# Flag used to select a model per run. Pi uses `--model <pattern>`.
PI_MODEL_ARGS = ["--model"]

# Dummy key so keyless LM Studio models are selectable in non-interactive mode.
# Set to None if your lmstudio provider already has an apiKey in models.json or
# you've authenticated with `/login`.
PI_API_KEY = "lmstudio"

# Print mode (non-interactive), ephemeral session, auto-trust the project dir so
# any project-local resources load without a prompt.
PI_BASE_ARGS = ["-p", "--no-session", "-a"]

PI_TIMEOUT = 900     # seconds allowed for one task attempt (the agent may iterate)

# --- models under test ----------------------------------------------------
# `pi_model` = model id EXACTLY as `pi --list-models` shows it (no provider prefix).
# `name`     = short label used in the report and results dir.
MODELS = [
    {"name": "gpt-oss-20b", "pi_model": "gpt-oss-20b"},
    {"name": "qwen3.5-9b",  "pi_model": "qwen/qwen3.5-9b"},
]

# --- run / grading --------------------------------------------------------
SAMPLES = 1          # attempts per task; raise for a stabler pass@1 estimate
GRADE_TIMEOUT = 20   # seconds for the hidden test to run
