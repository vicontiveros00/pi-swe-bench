# Unsubscribed handler still fires (and order is wrong)

## Bug report
An EventBus lets you subscribe(topic, handler) -> token, publish(topic, payload) which calls every current handler in subscription order and returns their results, and unsubscribe(token) which must stop that exact handler from firing (other handlers, even on the same topic, are unaffected). Failing: subscribe two handlers to a topic, unsubscribe the first, then publish — only the second handler should run, but both do.

## Task
Fix the bug so the tests pass. The bug may be in any of these files, and the symptom may surface far from its cause: `bus.py`, `registry.py`. Read them, find the real cause, and fix it there — do not merely patch the symptom or special-case the visible input. After each change, run `python test_public.py` and keep going until it prints `PASS`. Do not ask questions — make your best attempt. When the test passes, stop.
