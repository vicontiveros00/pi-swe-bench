"""Progressive bug-fixing suite for small local coding models.

Each task shows the model ONE failing example but is scored against a broader
hidden check set, so a model can't win by special-casing the shown input.

Fields:
  name       - short id
  tier       - 1 surface .. 5 algorithmic
  title      - human label
  entrypoint - the symbol the model must (re)define
  buggy      - code shown to the model
  spec       - intended behaviour + the one failing example
  check      - hidden assertions run against `mod` (the model's solution)
  reference  - a known-correct fix, used ONLY by validate.py
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
]
