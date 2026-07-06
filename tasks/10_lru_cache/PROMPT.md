# LRU cache recency on get

## Bug report
LRUCache(capacity) with get/put. get returns the value or -1 and must mark the key as most-recently-used; put evicts the least-recently-used key when full. Failing: after put(1,1), put(2,2), get(1), put(3,3) - key 2 should be evicted (1 was just used), but the buggy version evicts 1 because get doesn't update recency.

## Task
Fix the bug so the tests pass. Edit only `solution.py`. After each change, run `python test_public.py` and keep going until it prints `PASS`. Do not ask questions — make your best attempt. When the test passes, stop.
