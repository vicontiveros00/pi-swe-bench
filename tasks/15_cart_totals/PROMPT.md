# Cart total is wrong after applying a coupon

## Bug report
A Cart holds items priced in dollars and can apply a whole-percent coupon. total_cents() must equal the subtotal minus a coupon discount that is rounded HALF-UP to the nearest cent (standard retail rounding), never truncated. Failing: a cart with one item at $19.99 and a 10% coupon should total 1799 cents ($17.99) — discount 199.9→200 cents rounded half-up — but it returns 1800.

## Task
Fix the bug so the tests pass. The bug may be in any of these files, and the symptom may surface far from its cause: `cart.py`, `pricing.py`. Read them, find the real cause, and fix it there — do not merely patch the symptom or special-case the visible input. After each change, run `python test_public.py` and keep going until it prints `PASS`. Do not ask questions — make your best attempt. When the test passes, stop.
