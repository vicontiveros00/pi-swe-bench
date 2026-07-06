# Undo reverses a deposit

## Bug report
Ledger with deposit(amt) and undo(). undo() reverses the most recent deposit (subtracts it) and is a no-op with no history. Failing: after deposit(100), deposit(50), undo() the balance should be 100 but the buggy version gives 200.

## Task
Fix the bug so the tests pass. Edit only `solution.py`. After each change, run `python test_public.py` and keep going until it prints `PASS`. Do not ask questions — make your best attempt. When the test passes, stop.
