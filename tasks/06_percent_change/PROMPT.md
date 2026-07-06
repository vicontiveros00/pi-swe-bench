# Percent change, guard div-by-zero

## Bug report
percent_change(old, new) returns the percent change from old to new, or None if old is 0. Failing: percent_change(0, 5) should return None but raises ZeroDivisionError.

## Task
Fix the bug so the tests pass. Edit only `solution.py`. After each change, run `python test_public.py` and keep going until it prints `PASS`. Do not ask questions — make your best attempt. When the test passes, stop.
