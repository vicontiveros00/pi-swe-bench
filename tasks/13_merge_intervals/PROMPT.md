# Merge overlapping/touching intervals

## Bug report
merge_intervals(intervals) merges overlapping AND touching intervals ([1,2] and [2,3] merge into [1,3]) and returns them sorted as [start,end] lists. Failing: merge_intervals([[1,2],[2,3]]) should return [[1,3]] but the buggy version returns [[1,2],[2,3]].

## Task
Fix the bug so the tests pass. Edit only `solution.py`. After each change, run `python test_public.py` and keep going until it prints `PASS`. Do not ask questions — make your best attempt. When the test passes, stop.
