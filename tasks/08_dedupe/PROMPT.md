# Dedupe without mutating input

## Bug report
dedupe(lst) returns a NEW list with duplicates removed, preserving first-occurrence order, WITHOUT modifying the input. Failing: dedupe([1,2,1,3,2]) should return [1,2,3] and leave the input unchanged; the buggy version mutates the input and returns wrong results.

## Task
Fix the bug so the tests pass. Edit only `solution.py`. After each change, run `python test_public.py` and keep going until it prints `PASS`. Do not ask questions — make your best attempt. When the test passes, stop.
