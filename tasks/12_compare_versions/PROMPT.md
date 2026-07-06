# Compare dotted versions

## Bug report
compare_versions(a, b) compares dotted numeric version strings and returns -1, 0 or 1. Shorter versions are zero-padded; components are compared numerically (so '10' > '2'). Failing: compare_versions('1.2.1', '1.2') should return 1 but the buggy version returns 0 because it ignores the trailing component.

## Task
Fix the bug so the tests pass. Edit only `solution.py`. After each change, run `python test_public.py` and keep going until it prints `PASS`. Do not ask questions — make your best attempt. When the test passes, stop.
