#!/usr/bin/env python3
"""Sanity-check the suite. For every task:
  - the buggy solution must FAIL both the public and hidden tests
  - the reference solution must PASS both

Run this after editing tasks and regenerating (`python generate.py`).
"""
import json
import os
import shutil
import tempfile

from grade import run_test_file

ROOT = os.path.dirname(os.path.abspath(__file__))
MANIFEST = json.load(open(os.path.join(ROOT, "tasks", "manifest.json")))


def grade(solution_path, task):
    ws = tempfile.mkdtemp(prefix="pi-bench-val-")
    try:
        shutil.copy(solution_path, os.path.join(ws, "solution.py"))
        pub, _ = run_test_file(ws, os.path.join(ROOT, "tasks", task["dir"], "test_public.py"))
        hid, _ = run_test_file(ws, os.path.join(ROOT, "grading", task["dir"], "test_hidden.py"))
        return pub, hid
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def main():
    problems = 0
    for t in MANIFEST:
        buggy = os.path.join(ROOT, "tasks", t["dir"], "solution.py")
        ref = os.path.join(ROOT, "reference", t["dir"], "solution.py")
        b_pub, b_hid = grade(buggy, t)
        r_pub, r_hid = grade(ref, t)

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
