"""Benchmark configuration.

MODEL SELECTION (confirmed against a live LM Studio setup):
Pi selects models as `provider/model` and requires auth even for local servers.
For LM Studio you need BOTH:
  1. the provider prefix on the id  -> "lmstudio/gpt-oss-20b@f16"
  2. an api key for the provider    -> PI_API_KEY below (or `/login`)

Without the prefix, Pi guesses a provider (e.g. huggingface) and fails; without
the key it 401s or silently falls back to its defaultModel (that's the gemma load
we hit). Get the exact ids from `pi --list-models` and keep the `lmstudio/` prefix.
The pre-run preflight actually probes each model, so a bad id/key aborts early.
"""

# --- Pi invocation --------------------------------------------------------
PI_BIN = "pi"

# Pi selects a model with `--model <provider/model>`.
PI_MODEL_ARGS = ["--model"]

# Auth for the (keyless) LM Studio provider so its models are selectable.
# Set to None only if you've run `/login` for the lmstudio provider instead.
PI_API_KEY = "lmstudio"

# Print mode (non-interactive), ephemeral session, auto-trust the project dir.
PI_BASE_ARGS = ["-p", "--no-session", "-a"]

# --- sampling params ------------------------------------------------------
# Pi exposes no CLI flag for these; sampling.js (loaded via -e) stamps them onto
# every provider request through the before_provider_request hook. Set to None to
# leave a param at the provider/LM Studio default. These mirror a real agentic
# setup so the benchmark measures the model as you actually run it. Recorded in
# each run's metadata for reproducibility.
SAMPLING = {
    "temperature": 0.0,
    "top_p": 0.95,
    "top_k": 20,
    "min_p": 0.05,
    "presence_penalty": 1.5,
    "repeat_penalty": 1.0,
}

# Path to the extension that applies SAMPLING. Set to None to disable and fall
# back entirely to LM Studio's server-side defaults.
import os as _os
SAMPLING_EXTENSION = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "sampling.js")

PI_TIMEOUT = 120        # seconds per task attempt (the agent may iterate)
PREFLIGHT_TIMEOUT = 120 # seconds for the preflight probe (may JIT-load the model)

# LM Studio REST endpoint (the "Reachable at" address in LM Studio). If set, the
# preflight asks LM Studio which model actually loaded after each probe and FAILS
# if it isn't the one you asked for — this is what catches Pi silently falling back
# to its default model (e.g. gemma) when an id doesn't resolve. Set to None to skip.
LMSTUDIO_URL = "http://172.20.10.7:1234"

# --- models under test ----------------------------------------------------
# `pi_model` = provider-prefixed id EXACTLY as it works with `pi --model`.
# `name`     = short label used in the report and results dir.
MODELS = [
    {"name": "google/gemma-4-26b-a4b", "pi_model": "lmstudio/google/gemma-4-26b-a4b"},
    {"name": "gpt-oss-20b", "pi_model": "lmstudio/gpt-oss-20b"},
    {"name": "qwen/qwen3.5-9b", "pi_model": "lmstudio/qwen/qwen3.5-9b"},
]

# --- run / grading --------------------------------------------------------
SAMPLES = 1          # attempts per task; raise for a stabler pass@1 estimate
GRADE_TIMEOUT = 20   # seconds for the hidden test to run 