#!/usr/bin/env python3
"""Materialize the benchmark into a repo layout Pi can work in.

Reads task data from tasks.py and writes, for each task:
  tasks/<NN_name>/PROMPT.md       - task statement given to the agent
  tasks/<NN_name>/solution.py     - the buggy file the agent must fix (ONLY editable file)
  tasks/<NN_name>/test_public.py  - a runnable reproduction (the agent's target)
  grading/<NN_name>/test_hidden.py- broader held-out tests (grading; agent never sees these)
  reference/<NN_name>/solution.py - known-good fix (used only by validate.py)
  tasks/manifest.json             - id/dir/tier/title/entrypoint for the runner

Run:  python generate.py
"""
import json
import os
import textwrap

from prompts import build_prompt
from tasks import TASKS

ROOT = os.path.dirname(os.path.abspath(__file__))

# The single reproduction shown to the agent per task (the "failing example").
# Deliberately narrower than the hidden check set so hard-coding the example fails grading.
PUBLIC = {
    "chunk_list":       'assert solution.chunk_list([1,2,3,4,5], 2) == [[1,2],[3,4],[5]]',
    "clamp":            'assert solution.clamp(5, 0, 10) == 5',
    "mean":             'assert solution.mean([1,2]) == 1.5',
    "safe_head":        'assert solution.safe_head([]) is None',
    "binary_search":    'assert solution.binary_search([1,3,5,7], 7) == 3',
    "percent_change":   'assert solution.percent_change(0, 5) is None',
    "collect":          'assert solution.collect(1) == [1]\nassert solution.collect(2) == [2]',
    "dedupe":           'inp = [1,2,1,3,2]\nassert solution.dedupe(inp) == [1,2,3]\nassert inp == [1,2,1,3,2]',
    "round_half_up":    'assert solution.round_half_up(0.5) == 1\nassert solution.round_half_up(2.5) == 3',
    "lru_cache":        'c = solution.LRUCache(2)\nc.put(1,1); c.put(2,2)\nassert c.get(1) == 1\nc.put(3,3)\nassert c.get(2) == -1',
    "ledger":           'l = solution.Ledger()\nl.deposit(100); l.deposit(50)\nl.undo()\nassert l.balance == 100',
    "compare_versions": 'assert solution.compare_versions("1.2.1", "1.2") == 1',
    "merge_intervals":  'assert solution.merge_intervals([[1,2],[2,3]]) == [[1,3]]',
    "roman_to_int":     'assert solution.roman_to_int("IV") == 4',
}

TEST_TEMPLATE = '''import sys
import traceback

import solution


def run():
{body}


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
'''

def make_test(check_src):
    body = textwrap.indent(textwrap.dedent(check_src).strip("\n").replace("mod.", "solution."), "    ")
    return TEST_TEMPLATE.format(body=body)


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content if content.endswith("\n") else content + "\n")


def main():
    manifest = []
    for i, t in enumerate(TASKS, 1):
        slug = t["name"]
        d = f"{i:02d}_{slug}"

        write(os.path.join(ROOT, "tasks", d, "solution.py"),
              textwrap.dedent(t["buggy"]).strip("\n"))
        write(os.path.join(ROOT, "tasks", d, "test_public.py"),
              make_test(PUBLIC[slug]))
        write(os.path.join(ROOT, "tasks", d, "PROMPT.md"),
              build_prompt("standard", t["title"], t["spec"], t["entrypoint"]))
        write(os.path.join(ROOT, "grading", d, "test_hidden.py"),
              make_test(t["check"]))
        write(os.path.join(ROOT, "reference", d, "solution.py"),
              textwrap.dedent(t["reference"]).strip("\n"))

        manifest.append({
            "id": slug, "dir": d, "tier": t["tier"],
            "title": t["title"], "entrypoint": t["entrypoint"],
            "spec": t["spec"].strip(),
        })

    write(os.path.join(ROOT, "tasks", "manifest.json"),
          json.dumps(manifest, indent=2))
    print(f"Materialized {len(manifest)} tasks into tasks/, grading/, reference/")


if __name__ == "__main__":
    main()
