"""Progressive bug-fixing suite for small local coding models.

Each task shows the model ONE failing example but is scored against a broader
hidden check set, so a model can't win by special-casing the shown input.

Fields:
  name       - short id
  tier       - 1 surface .. 5 algorithmic .. 6 multi-file diagnosis
  title      - human label
  entrypoint - the symbol the model must (re)define
  buggy      - code shown to the model
  spec       - intended behaviour + the one failing example
  check      - hidden assertions run against `mod` (the model's solution)
  reference  - a known-correct fix, used ONLY by validate.py

Multi-file tasks (tier 6) use these instead of buggy/reference:
  files          - {filename: source} for the whole starter repo (buggy state)
  reference_files- {filename: source} the known-good repo (validate.py only)
  editable       - list of filenames the agent is allowed to edit (informational;
                   the grader only cares about final repo state)
  entry_module   - the module the tests import (default "solution"); its .py is
                   what test_public/test_hidden do `import <entry_module>` on
A single-file task is just sugar for files={entry_module+".py": buggy} and
reference_files={entry_module+".py": reference}; the generator normalizes both
shapes to `files`, so downstream code only deals with file dicts.
"""

TASKS = [
    # ---------------- Tier 1: surface bugs ----------------
    {
        "name": "chunk_list", "tier": 1, "title": "Split list into chunks",
        "entrypoint": "chunk_list",
        "buggy": '''
def chunk_list(lst, n):
    result = []
    for i in range(0, len(lst) // n * n, n):
        result.append(lst[i:i+n])
    return result
''',
        "spec": "chunk_list(lst, n) splits lst into consecutive chunks of size n. "
                "The final chunk may be shorter. "
                "Failing: chunk_list([1,2,3,4,5], 2) should be [[1,2],[3,4],[5]] "
                "but the buggy version drops [5].",
        "check": '''
assert mod.chunk_list([1,2,3,4,5],2) == [[1,2],[3,4],[5]]
assert mod.chunk_list([1,2,3,4],2) == [[1,2],[3,4]]
assert mod.chunk_list([1,2,3],1) == [[1],[2],[3]]
assert mod.chunk_list([],3) == []
assert mod.chunk_list([1,2,3,4,5,6,7],3) == [[1,2,3],[4,5,6],[7]]
''',
        "reference": '''
def chunk_list(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]
''',
    },
    {
        "name": "clamp", "tier": 1, "title": "Clamp a value to a range",
        "entrypoint": "clamp",
        "buggy": '''
def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x < hi:
        return hi
    return x
''',
        "spec": "clamp(x, lo, hi) returns x limited to [lo, hi]. "
                "Failing: clamp(5, 0, 10) should return 5 but returns 10.",
        "check": '''
assert mod.clamp(5,0,10) == 5
assert mod.clamp(-3,0,10) == 0
assert mod.clamp(15,0,10) == 10
assert mod.clamp(0,0,10) == 0
assert mod.clamp(10,0,10) == 10
''',
        "reference": '''
def clamp(x, lo, hi):
    if x < lo: return lo
    if x > hi: return hi
    return x
''',
    },
    {
        "name": "mean", "tier": 1, "title": "Arithmetic mean",
        "entrypoint": "mean",
        "buggy": '''
def mean(nums):
    return sum(nums) // len(nums)
''',
        "spec": "mean(nums) returns the arithmetic mean as a float. "
                "Failing: mean([1,2]) should be 1.5 but the buggy version returns 1.",
        "check": '''
assert mod.mean([1,2]) == 1.5
assert mod.mean([2,2,2]) == 2
assert abs(mod.mean([1,2,4]) - 7/3) < 1e-9
assert mod.mean([10]) == 10
''',
        "reference": '''
def mean(nums):
    return sum(nums) / len(nums)
''',
    },
    # ---------------- Tier 2: edge cases ----------------
    {
        "name": "safe_head", "tier": 2, "title": "First element or None",
        "entrypoint": "safe_head",
        "buggy": '''
def safe_head(lst):
    return lst[0]
''',
        "spec": "safe_head(lst) returns the first element, or None if lst is empty. "
                "Failing: safe_head([]) should return None but raises IndexError.",
        "check": '''
assert mod.safe_head([1,2,3]) == 1
assert mod.safe_head([]) is None
assert mod.safe_head(["a"]) == "a"
''',
        "reference": '''
def safe_head(lst):
    return lst[0] if lst else None
''',
    },
    {
        "name": "binary_search", "tier": 2, "title": "Binary search index",
        "entrypoint": "binary_search",
        "buggy": '''
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
''',
        "spec": "binary_search(arr, target) on an ascending sorted list returns the "
                "index of target, else -1. "
                "Failing: binary_search([1,3,5,7], 7) should return 3 but returns -1.",
        "check": '''
a = [1,3,5,7,9,11]
for i, v in enumerate(a):
    assert mod.binary_search(a, v) == i
assert mod.binary_search(a, 4) == -1
assert mod.binary_search([], 1) == -1
assert mod.binary_search([2], 2) == 0
''',
        "reference": '''
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target: return mid
        elif arr[mid] < target: lo = mid + 1
        else: hi = mid - 1
    return -1
''',
    },
    {
        "name": "percent_change", "tier": 2, "title": "Percent change, guard div-by-zero",
        "entrypoint": "percent_change",
        "buggy": '''
def percent_change(old, new):
    return (new - old) / old * 100
''',
        "spec": "percent_change(old, new) returns the percent change from old to new, "
                "or None if old is 0. "
                "Failing: percent_change(0, 5) should return None but raises ZeroDivisionError.",
        "check": '''
assert mod.percent_change(100,150) == 50
assert mod.percent_change(0,5) is None
assert mod.percent_change(200,100) == -50
''',
        "reference": '''
def percent_change(old, new):
    if old == 0: return None
    return (new - old) / old * 100
''',
    },
    # ---------------- Tier 3: subtle semantics ----------------
    {
        "name": "collect", "tier": 3, "title": "Mutable default argument",
        "entrypoint": "collect",
        "buggy": '''
def collect(item, bucket=[]):
    bucket.append(item)
    return bucket
''',
        "spec": "collect(item) with no bucket should return a fresh list with only item. "
                "Failing: collect(1) then collect(2) - the second call should return [2], "
                "but the buggy version returns [1,2] because it reuses one default list.",
        "check": '''
assert mod.collect(1) == [1]
assert mod.collect(2) == [2]
assert mod.collect(3) == [3]
assert mod.collect(20, [10]) == [10, 20]
''',
        "reference": '''
def collect(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket
''',
    },
    {
        "name": "dedupe", "tier": 3, "title": "Dedupe without mutating input",
        "entrypoint": "dedupe",
        "buggy": '''
def dedupe(lst):
    seen = set()
    for x in lst:
        if x in seen:
            lst.remove(x)
        seen.add(x)
    return lst
''',
        "spec": "dedupe(lst) returns a NEW list with duplicates removed, preserving "
                "first-occurrence order, WITHOUT modifying the input. "
                "Failing: dedupe([1,2,1,3,2]) should return [1,2,3] and leave the input "
                "unchanged; the buggy version mutates the input and returns wrong results.",
        "check": '''
inp = [1,2,1,3,2]
out = mod.dedupe(inp)
assert out == [1,2,3]
assert inp == [1,2,1,3,2]
assert mod.dedupe([]) == []
assert mod.dedupe([5,5,5]) == [5]
''',
        "reference": '''
def dedupe(lst):
    seen = set()
    out = []
    for x in lst:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out
''',
    },
    {
        "name": "round_half_up", "tier": 3, "title": "Round halves up (not banker's)",
        "entrypoint": "round_half_up",
        "buggy": '''
def round_half_up(x):
    return round(x)
''',
        "spec": "round_half_up(x) rounds to the nearest integer, rounding halves UP. "
                "Failing: round_half_up(0.5) should be 1 and round_half_up(2.5) should be 3, "
                "but Python's round() uses banker's rounding and returns 0 and 2.",
        "check": '''
assert mod.round_half_up(0.5) == 1
assert mod.round_half_up(2.5) == 3
assert mod.round_half_up(1.4) == 1
assert mod.round_half_up(1.6) == 2
assert mod.round_half_up(3) == 3
''',
        "reference": '''
import math
def round_half_up(x):
    return math.floor(x + 0.5)
''',
    },
    # ---------------- Tier 4: stateful / multi-method ----------------
    {
        "name": "lru_cache", "tier": 4, "title": "LRU cache recency on get",
        "entrypoint": "LRUCache",
        "buggy": '''
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = {}
        self.order = []
    def get(self, key):
        return self.data.get(key, -1)
    def put(self, key, value):
        if key in self.data:
            self.order.remove(key)
        elif len(self.data) >= self.capacity:
            oldest = self.order.pop(0)
            del self.data[oldest]
        self.data[key] = value
        self.order.append(key)
''',
        "spec": "LRUCache(capacity) with get/put. get returns the value or -1 and must "
                "mark the key as most-recently-used; put evicts the least-recently-used "
                "key when full. "
                "Failing: after put(1,1), put(2,2), get(1), put(3,3) - key 2 should be "
                "evicted (1 was just used), but the buggy version evicts 1 because get "
                "doesn't update recency.",
        "check": '''
c = mod.LRUCache(2)
c.put(1,1); c.put(2,2)
assert c.get(1) == 1
c.put(3,3)                 # evict 2
assert c.get(2) == -1
assert c.get(3) == 3
assert c.get(1) == 1       # order now [3,1]
c.put(4,4)                 # evict 3
assert c.get(3) == -1
assert c.get(4) == 4
assert c.get(1) == 1
''',
        "reference": '''
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = {}
        self.order = []
    def get(self, key):
        if key in self.data:
            self.order.remove(key)
            self.order.append(key)
            return self.data[key]
        return -1
    def put(self, key, value):
        if key in self.data:
            self.order.remove(key)
        elif len(self.data) >= self.capacity:
            oldest = self.order.pop(0)
            del self.data[oldest]
        self.data[key] = value
        self.order.append(key)
''',
    },
    {
        "name": "ledger", "tier": 4, "title": "Undo reverses a deposit",
        "entrypoint": "Ledger",
        "buggy": '''
class Ledger:
    def __init__(self):
        self.balance = 0
        self.history = []
    def deposit(self, amt):
        self.balance += amt
        self.history.append(amt)
    def undo(self):
        if self.history:
            last = self.history.pop()
            self.balance += last
''',
        "spec": "Ledger with deposit(amt) and undo(). undo() reverses the most recent "
                "deposit (subtracts it) and is a no-op with no history. "
                "Failing: after deposit(100), deposit(50), undo() the balance should be "
                "100 but the buggy version gives 200.",
        "check": '''
l = mod.Ledger()
l.deposit(100); l.deposit(50)
l.undo()
assert l.balance == 100
l.undo()
assert l.balance == 0
l.undo()
assert l.balance == 0
''',
        "reference": '''
class Ledger:
    def __init__(self):
        self.balance = 0
        self.history = []
    def deposit(self, amt):
        self.balance += amt
        self.history.append(amt)
    def undo(self):
        if self.history:
            last = self.history.pop()
            self.balance -= last
''',
    },
    # ---------------- Tier 5: algorithmic ----------------
    {
        "name": "compare_versions", "tier": 5, "title": "Compare dotted versions",
        "entrypoint": "compare_versions",
        "buggy": '''
def compare_versions(a, b):
    pa = [int(x) for x in a.split(".")]
    pb = [int(x) for x in b.split(".")]
    for i in range(min(len(pa), len(pb))):
        if pa[i] < pb[i]:
            return -1
        if pa[i] > pb[i]:
            return 1
    return 0
''',
        "spec": "compare_versions(a, b) compares dotted numeric version strings and "
                "returns -1, 0 or 1. Shorter versions are zero-padded; components are "
                "compared numerically (so '10' > '2'). "
                "Failing: compare_versions('1.2.1', '1.2') should return 1 but the buggy "
                "version returns 0 because it ignores the trailing component.",
        "check": '''
assert mod.compare_versions("1.2.1","1.2") == 1
assert mod.compare_versions("1.2","1.2.1") == -1
assert mod.compare_versions("1.0","1") == 0
assert mod.compare_versions("2.0","10.0") == -1
assert mod.compare_versions("1.2.3","1.2.3") == 0
''',
        "reference": '''
def compare_versions(a, b):
    pa = [int(x) for x in a.split(".")]
    pb = [int(x) for x in b.split(".")]
    n = max(len(pa), len(pb))
    pa += [0] * (n - len(pa))
    pb += [0] * (n - len(pb))
    for x, y in zip(pa, pb):
        if x < y: return -1
        if x > y: return 1
    return 0
''',
    },
    {
        "name": "merge_intervals", "tier": 5, "title": "Merge overlapping/touching intervals",
        "entrypoint": "merge_intervals",
        "buggy": '''
def merge_intervals(intervals):
    intervals = sorted(intervals)
    merged = []
    for start, end in intervals:
        if merged and start < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
''',
        "spec": "merge_intervals(intervals) merges overlapping AND touching intervals "
                "([1,2] and [2,3] merge into [1,3]) and returns them sorted as [start,end] "
                "lists. "
                "Failing: merge_intervals([[1,2],[2,3]]) should return [[1,3]] but the "
                "buggy version returns [[1,2],[2,3]].",
        "check": '''
assert mod.merge_intervals([[1,2],[2,3]]) == [[1,3]]
assert mod.merge_intervals([[1,4],[2,3]]) == [[1,4]]
assert mod.merge_intervals([[1,2],[3,4]]) == [[1,2],[3,4]]
assert mod.merge_intervals([[3,4],[1,2],[2,3]]) == [[1,4]]
assert mod.merge_intervals([]) == []
''',
        "reference": '''
def merge_intervals(intervals):
    intervals = sorted(intervals)
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
''',
    },
    {
        "name": "roman_to_int", "tier": 5, "title": "Roman numeral to int",
        "entrypoint": "roman_to_int",
        "buggy": '''
def roman_to_int(s):
    vals = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
    total = 0
    for ch in s:
        total += vals[ch]
    return total
''',
        "spec": "roman_to_int(s) converts a Roman numeral to an integer, handling "
                "subtractive pairs (IV=4, IX=9, XL=40, ...). "
                "Failing: roman_to_int('IV') should return 4 but the buggy version returns 6.",
        "check": '''
assert mod.roman_to_int("III") == 3
assert mod.roman_to_int("IV") == 4
assert mod.roman_to_int("IX") == 9
assert mod.roman_to_int("LVIII") == 58
assert mod.roman_to_int("MCMXCIV") == 1994
''',
        "reference": '''
def roman_to_int(s):
    vals = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
    total = 0
    for i, ch in enumerate(s):
        if i + 1 < len(s) and vals[ch] < vals[s[i+1]]:
            total -= vals[ch]
        else:
            total += vals[ch]
    return total
''',
    },

    # ---------------- Tier 6: multi-file diagnosis ----------------
    # These are the tie-breakers. The SYMPTOM (what the public test shows) lives
    # in a different file from the CAUSE. The tempting one-line patch at the
    # symptom site passes test_public but fails the wider hidden set, which only
    # a fix at the true cause satisfies. Meant to be run at --guidance auto
    # (no bug report), so the model must reproduce -> localize -> fix.
    {
        "name": "cart_totals", "tier": 6,
        "title": "Cart total is wrong after applying a coupon",
        "entrypoint": "Cart",
        "entry_module": "cart",
        "editable": ["cart.py", "pricing.py"],
        "files": {
            "pricing.py": '''
# Money is handled in integer cents everywhere to avoid float drift.

def to_cents(dollars):
    # dollars may be int or float like 19.99
    return int(round(dollars * 100))


def apply_percent_off(cents, percent):
    # percent is an int 0..100. Returns the DISCOUNTED price in cents.
    # BUG: truncates toward zero, and rounds the discount instead of the price,
    # so results drift by a cent on odd totals.
    discount = int(cents * percent / 100)
    return cents - discount


def format_money(cents):
    return "${:.2f}".format(cents / 100)
''',
            "cart.py": '''
from pricing import to_cents, apply_percent_off, format_money


class Cart:
    def __init__(self):
        self._items = []          # list of (name, unit_cents, qty)
        self._percent_off = 0

    def add(self, name, unit_price, qty=1):
        self._items.append((name, to_cents(unit_price), qty))

    def apply_coupon(self, percent):
        self._percent_off = percent

    def subtotal_cents(self):
        return sum(unit * qty for _, unit, qty in self._items)

    def total_cents(self):
        sub = self.subtotal_cents()
        if self._percent_off:
            return apply_percent_off(sub, self._percent_off)
        return sub

    def total(self):
        return format_money(self.total_cents())
''',
        },
        "spec": "A Cart holds items priced in dollars and can apply a whole-percent "
                "coupon. total_cents() must equal the subtotal minus a coupon discount "
                "that is rounded HALF-UP to the nearest cent (standard retail rounding), "
                "never truncated. Failing: a cart with one item at $19.99 and a 10% coupon "
                "should total 1799 cents ($17.99) \u2014 discount 199.9\u2192200 cents rounded "
                "half-up \u2014 but it returns 1800.",
        "check": '''
import cart as C

# one item, 10% off: 1999c, discount 199.9 -> 200 (half-up) -> 1799
c = C.Cart()
c.add("widget", 19.99)
c.apply_coupon(10)
assert c.total_cents() == 1799, c.total_cents()
assert c.total() == "$17.99"

# no coupon -> exact subtotal
c = C.Cart()
c.add("a", 10.00, 2)
c.add("b", 5.55)
assert c.total_cents() == 2555

# discount rounds half-up: 3333c * 15% = 499.95 -> 500 -> 2833
c = C.Cart()
c.add("x", 33.33)
c.apply_coupon(15)
assert c.total_cents() == 2833, c.total_cents()

# 100% off is free; 0% off is a no-op
c = C.Cart(); c.add("y", 12.34); c.apply_coupon(100)
assert c.total_cents() == 0
c = C.Cart(); c.add("z", 12.34); c.apply_coupon(0)
assert c.total_cents() == 1234

# exact-half boundary rounds up: 2000c * 25% = 500.0 -> 500 -> 1500
c = C.Cart(); c.add("h", 20.00); c.apply_coupon(25)
assert c.total_cents() == 1500

# HALF-UP the DISCOUNT, not banker's and not "round the kept price".
# $3.30 @ 25%: discount 82.5 -> half-up 83 -> total 247.
# Banker's discount = 82 -> 248; rounding the kept price (247.5) -> 248 too.
# So only rounding the DISCOUNT half-up yields 247.
c = C.Cart(); c.add("hu1", 3.30); c.apply_coupon(25)
assert c.total_cents() == 247, c.total_cents()

# $10.10 @ 25%: discount 252.5 -> half-up 253 -> total 757
# (banker's / price-rounding both give 758).
c = C.Cart(); c.add("hu2", 10.10); c.apply_coupon(25)
assert c.total_cents() == 757, c.total_cents()

# quantities and coupon together: (1001*3)=3003, 33% -> 990.99 -> 991 -> 2012
c = C.Cart(); c.add("q", 10.01, 3); c.apply_coupon(33)
assert c.total_cents() == 2012, c.total_cents()
''',
        "reference_files": {
            "pricing.py": '''
import math


def to_cents(dollars):
    return int(round(dollars * 100))


def apply_percent_off(cents, percent):
    # round the DISCOUNT half-up, then subtract, so the price is exact to the cent
    discount = math.floor(cents * percent / 100 + 0.5)
    return cents - discount


def format_money(cents):
    return "${:.2f}".format(cents / 100)
''',
            "cart.py": '''
from pricing import to_cents, apply_percent_off, format_money


class Cart:
    def __init__(self):
        self._items = []
        self._percent_off = 0

    def add(self, name, unit_price, qty=1):
        self._items.append((name, to_cents(unit_price), qty))

    def apply_coupon(self, percent):
        self._percent_off = percent

    def subtotal_cents(self):
        return sum(unit * qty for _, unit, qty in self._items)

    def total_cents(self):
        sub = self.subtotal_cents()
        if self._percent_off:
            return apply_percent_off(sub, self._percent_off)
        return sub

    def total(self):
        return format_money(self.total_cents())
''',
        },
    },
    {
        "name": "event_bus", "tier": 6,
        "title": "Unsubscribed handler still fires (and order is wrong)",
        "entrypoint": "EventBus",
        "entry_module": "bus",
        "editable": ["bus.py", "registry.py"],
        "files": {
            "registry.py": '''
# Tracks handlers per topic, preserving subscription order.

class Registry:
    def __init__(self):
        self._by_topic = {}   # topic -> list of (token, handler)
        self._next = 1

    def add(self, topic, handler):
        token = self._next
        self._next += 1
        self._by_topic.setdefault(topic, []).append((token, handler))
        return token

    def remove(self, token):
        # BUG: only removes from the FIRST topic that has a matching token and
        # then keeps scanning, but compares token to the handler tuple, so it
        # never actually matches -> nothing is ever removed.
        for topic, entries in self._by_topic.items():
            for e in entries:
                if e == token:
                    entries.remove(e)

    def handlers(self, topic):
        return [h for _, h in self._by_topic.get(topic, [])]
''',
            "bus.py": '''
from registry import Registry


class EventBus:
    def __init__(self):
        self._reg = Registry()

    def subscribe(self, topic, handler):
        return self._reg.add(topic, handler)

    def unsubscribe(self, token):
        self._reg.remove(token)

    def publish(self, topic, payload):
        # call each subscribed handler in subscription order; collect results
        results = []
        for h in self._reg.handlers(topic):
            results.append(h(payload))
        return results
''',
        },
        "spec": "An EventBus lets you subscribe(topic, handler) -> token, publish(topic, "
                "payload) which calls every current handler in subscription order and "
                "returns their results, and unsubscribe(token) which must stop that "
                "exact handler from firing (other handlers, even on the same topic, are "
                "unaffected). Failing: subscribe two handlers to a topic, unsubscribe the "
                "first, then publish \u2014 only the second handler should run, but both do.",
        "check": '''
import bus as B

calls = []
bus = B.EventBus()
t1 = bus.subscribe("n", lambda p: calls.append(("a", p)) or "a")
t2 = bus.subscribe("n", lambda p: calls.append(("b", p)) or "b")

# order preserved, both fire
assert bus.publish("n", 1) == ["a", "b"]
assert calls == [("a", 1), ("b", 1)]

# unsubscribe the FIRST; only the second may fire now
calls.clear()
bus.unsubscribe(t1)
assert bus.publish("n", 2) == ["b"]
assert calls == [("b", 2)]

# unsubscribing an unknown/already-removed token is a harmless no-op
bus.unsubscribe(t1)
bus.unsubscribe(9999)
assert bus.publish("n", 3) == ["b"]

# topics are isolated; a token only removes its own handler
bus2 = B.EventBus()
x = bus2.subscribe("x", lambda p: "x")
y = bus2.subscribe("y", lambda p: "y")
bus2.unsubscribe(x)
assert bus2.publish("x", 0) == []
assert bus2.publish("y", 0) == ["y"]

# re-subscribing after removal restores firing, in new subscription order
z = bus.subscribe("n", lambda p: "c")
assert bus.publish("n", 4) == ["b", "c"]
''',
        "reference_files": {
            "registry.py": '''
class Registry:
    def __init__(self):
        self._by_topic = {}
        self._next = 1

    def add(self, topic, handler):
        token = self._next
        self._next += 1
        self._by_topic.setdefault(topic, []).append((token, handler))
        return token

    def remove(self, token):
        for topic, entries in self._by_topic.items():
            self._by_topic[topic] = [(t, h) for (t, h) in entries if t != token]

    def handlers(self, topic):
        return [h for _, h in self._by_topic.get(topic, [])]
''',
            "bus.py": '''
from registry import Registry


class EventBus:
    def __init__(self):
        self._reg = Registry()

    def subscribe(self, topic, handler):
        return self._reg.add(topic, handler)

    def unsubscribe(self, token):
        self._reg.remove(token)

    def publish(self, topic, payload):
        results = []
        for h in self._reg.handlers(topic):
            results.append(h(payload))
        return results
''',
        },
    },
    {
        "name": "paginate", "tier": 6,
        "title": "Last page of results is dropped",
        "entrypoint": "paginate",
        "entry_module": "service",
        "editable": ["service.py", "page_math.py"],
        "files": {
            "page_math.py": '''
# Pure pagination arithmetic, shared by several services.

def page_count(total, per_page):
    # number of pages needed to show `total` items, `per_page` per page.
    # BUG: integer division floors, so a partial final page is lost
    # (13 items / 5 per page -> 2, but you need 3).
    return total // per_page


def slice_bounds(page, per_page):
    # (start, end) indices for a 1-based page number.
    start = (page - 1) * per_page
    return start, start + per_page
''',
            "service.py": '''
from page_math import page_count, slice_bounds


def paginate(items, page, per_page):
    \"\"\"Return a dict describing one page of `items`.

    {"items": [...], "page": p, "pages": total_pages, "total": n}
    Pages are 1-based. Out-of-range pages yield an empty item list but still
    report the correct total page count. per_page is assumed >= 1.
    \"\"\"
    n = len(items)
    pages = page_count(n, per_page)
    start, end = slice_bounds(page, per_page)
    return {"items": items[start:end], "page": page, "pages": pages, "total": n}
''',
        },
        "spec": "paginate(items, page, per_page) returns {'items','page','pages','total'} "
                "for a 1-based page. 'pages' is the total number of pages needed to show "
                "every item, INCLUDING a short final page. Failing: paginate(list(range(13)), "
                "3, 5) should report pages=3 and items=[10,11,12], but it reports pages=2 "
                "and an empty final page.",
        "check": '''
import service as S

r = S.paginate(list(range(13)), 3, 5)
assert r["pages"] == 3, r["pages"]
assert r["items"] == [10, 11, 12]
assert r["page"] == 3 and r["total"] == 13

# exact multiple: 10 items / 5 -> exactly 2 pages, no phantom 3rd
r = S.paginate(list(range(10)), 2, 5)
assert r["pages"] == 2
assert r["items"] == [5, 6, 7, 8, 9]

# first page
r = S.paginate(list(range(13)), 1, 5)
assert r["items"] == [0, 1, 2, 3, 4] and r["pages"] == 3

# out-of-range page: empty items, but page count still correct
r = S.paginate(list(range(13)), 4, 5)
assert r["items"] == [] and r["pages"] == 3

# empty input -> zero pages, empty page
r = S.paginate([], 1, 5)
assert r["items"] == [] and r["pages"] == 0 and r["total"] == 0

# single short page
r = S.paginate([1, 2, 3], 1, 10)
assert r["items"] == [1, 2, 3] and r["pages"] == 1
''',
        "reference_files": {
            "page_math.py": '''
def page_count(total, per_page):
    return (total + per_page - 1) // per_page


def slice_bounds(page, per_page):
    start = (page - 1) * per_page
    return start, start + per_page
''',
            "service.py": '''
from page_math import page_count, slice_bounds


def paginate(items, page, per_page):
    \"\"\"Return a dict describing one page of `items`.

    {"items": [...], "page": p, "pages": total_pages, "total": n}
    Pages are 1-based. Out-of-range pages yield an empty item list but still
    report the correct total page count. per_page is assumed >= 1.
    \"\"\"
    n = len(items)
    pages = page_count(n, per_page)
    start, end = slice_bounds(page, per_page)
    return {"items": items[start:end], "page": page, "pages": pages, "total": n}
''',
        },
    },
]
