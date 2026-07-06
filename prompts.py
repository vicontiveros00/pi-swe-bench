"""Prompt construction for the three guidance levels.

Guidance controls how much the agent is told, so you can separate *finding* the
bug from *fixing* it:

  auto     - symptom only ("the tests are failing, fix it"). Hardest; tests
             diagnosis. No bug report, no function name.
  standard - a bug report (the default; matches the materialized PROMPT.md).
  guided   - names the buggy function/class. Isolates fix ability from
             localization.

The reasoning regime (gpt-oss effort / Qwen thinking mode) is a SEPARATE,
model-level lever set in your Pi / LM Studio config, not here. Keep these prompts
model-agnostic so the only thing that differs between models is the model.
"""

GUIDANCE_LEVELS = ("auto", "standard", "guided")

# Shared behavioural footer: the edit->run->iterate loop plus "don't hang on a
# question", which matter a lot for small models in headless mode.
_FOOTER = (
    "Edit only `solution.py`. After each change, run `python test_public.py` and "
    "keep going until it prints `PASS`. Do not ask questions \u2014 make your best "
    "attempt. When the test passes, stop."
)

_AUTO = """# Failing tests

The tests in this project are failing because of a bug in `solution.py`.
Find the cause and fix it. {footer}
"""

_STANDARD = """# {title}

## Bug report
{spec}

## Task
Fix the bug so the tests pass. {footer}
"""

_GUIDED = """# {title}

The bug is in `{entrypoint}` in `solution.py`.

## Expected behaviour
{spec}

## Task
Fix `{entrypoint}` so the tests pass. {footer}
"""


def build_prompt(guidance, title, spec, entrypoint):
    """Return the task prompt for the given guidance level."""
    if guidance not in GUIDANCE_LEVELS:
        raise ValueError(f"unknown guidance {guidance!r}; expected one of {GUIDANCE_LEVELS}")
    spec = spec.strip()
    if guidance == "auto":
        return _AUTO.format(footer=_FOOTER)
    if guidance == "guided":
        return _GUIDED.format(title=title, spec=spec, entrypoint=entrypoint, footer=_FOOTER)
    return _STANDARD.format(title=title, spec=spec, footer=_FOOTER)
