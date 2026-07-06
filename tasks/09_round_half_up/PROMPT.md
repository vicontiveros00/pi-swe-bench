# Round halves up (not banker's)

## Bug report
round_half_up(x) rounds to the nearest integer, rounding halves UP. Failing: round_half_up(0.5) should be 1 and round_half_up(2.5) should be 3, but Python's round() uses banker's rounding and returns 0 and 2.

## Task
Fix the bug so the tests pass. Edit only `solution.py`. After each change, run `python test_public.py` and keep going until it prints `PASS`. Do not ask questions — make your best attempt. When the test passes, stop.
