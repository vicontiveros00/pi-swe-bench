# Last page of results is dropped

## Bug report
paginate(items, page, per_page) returns {'items','page','pages','total'} for a 1-based page. 'pages' is the total number of pages needed to show every item, INCLUDING a short final page. Failing: paginate(list(range(13)), 3, 5) should report pages=3 and items=[10,11,12], but it reports pages=2 and an empty final page.

## Task
Fix the bug so the tests pass. The bug may be in any of these files, and the symptom may surface far from its cause: `service.py`, `page_math.py`. Read them, find the real cause, and fix it there — do not merely patch the symptom or special-case the visible input. After each change, run `python test_public.py` and keep going until it prints `PASS`. Do not ask questions — make your best attempt. When the test passes, stop.
