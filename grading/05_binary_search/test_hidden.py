import sys
import traceback

import solution


def run():
    a = [1,3,5,7,9,11]
    for i, v in enumerate(a):
        assert solution.binary_search(a, v) == i
    assert solution.binary_search(a, 4) == -1
    assert solution.binary_search([], 1) == -1
    assert solution.binary_search([2], 2) == 0


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
