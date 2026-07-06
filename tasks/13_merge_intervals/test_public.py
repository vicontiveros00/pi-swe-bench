import sys
import traceback

import solution


def run():
    assert solution.merge_intervals([[1,2],[2,3]]) == [[1,3]]


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
