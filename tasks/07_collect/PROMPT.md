# Mutable default argument

## Bug report
collect(item) with no bucket should return a fresh list with only item. Failing: collect(1) then collect(2) - the second call should return [2], but the buggy version returns [1,2] because it reuses one default list.

## Task
Fix the bug so the tests pass. Edit only `solution.py`. After each change, run `python test_public.py` and keep going until it prints `PASS`. Do not ask questions — make your best attempt. When the test passes, stop.
