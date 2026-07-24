#!/usr/bin/env python3
"""Sanity-check the suite. For every task:
  - the buggy repo must FAIL both the public and hidden tests
  - the reference repo must PASS both

Works for single-file tasks (solution.py) and multi-file tier-6 tasks (whole
starter repo). The buggy files live under tasks/<dir>/, the fixed files under
reference/<dir>/; we lay the right set into a temp workspace and run the tests
there so imports resolve to the files under test.

Run this after editing tasks and regenerating (`python generate.py`).
"""
import json
import os
import shutil
import tempfile

from grade import run_test_file

ROOT = os.path.dirname(os.path.abspath(__file__))
MANIFEST = json.load(open(os.path.join(ROOT, "tasks", "manifest.json")))


def grade(source_dir, task):
    """Lay every task .py file from source_dir into a fresh workspace, then run
    the public and hidden tests against it. source_dir is tasks/<dir> (buggy) or
    reference/<dir> (fixed)."""
    ws = tempfile.mkdtemp(prefix="pi-bench-val-")
    try:
        for fn in task["files"]:
            shutil.copy(os.path.join(source_dir, fn), os.path.join(ws, fn))
        pub, _ = run_test_file(ws, os.path.join(ROOT, "tasks", task["dir"], "test_public.py"))
        hid, _ = run_test_file(ws, os.path.join(ROOT, "grading", task["dir"], "test_hidden.py"))
        return pub, hid
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def main():
    problems = 0
    for t in MANIFEST:
        b_pub, b_hid = grade(os.path.join(ROOT, "tasks", t["dir"]), t)
        r_pub, r_hid = grade(os.path.join(ROOT, "reference", t["dir"]), t)

        flags = []
        if b_pub or b_hid:
            flags.append("BUG-NOT-CAUGHT")
        if not (r_pub and r_hid):
            flags.append("REF-FAILS")
        if flags:
            problems += 1
        status = "OK" if not flags else " ".join(flags)
        print(f"T{t['tier']} {t['dir']:<22} "
              f"buggy(pub={b_pub!s:<5} hid={b_hid!s:<5})  "
              f"ref(pub={r_pub!s:<5} hid={r_hid!s:<5})  {status}")

    print()
    print("ALL GOOD" if problems == 0 else f"{problems} problem(s) found")


if __name__ == "__main__":
    main()
