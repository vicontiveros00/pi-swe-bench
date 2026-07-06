import sys
import traceback

import solution


def run():
    c = solution.LRUCache(2)
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


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
