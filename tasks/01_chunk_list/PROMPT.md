# Split list into chunks

## Bug report
chunk_list(lst, n) splits lst into consecutive chunks of size n. The final chunk may be shorter. Failing: chunk_list([1,2,3,4,5], 2) should be [[1,2],[3,4],[5]] but the buggy version drops [5].

## Task
Fix the bug so the tests pass. Edit only `solution.py`. After each change, run `python test_public.py` and keep going until it prints `PASS`. Do not ask questions — make your best attempt. When the test passes, stop.
