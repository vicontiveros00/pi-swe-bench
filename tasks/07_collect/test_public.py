import sys
import traceback

import solution


def run():
    assert solution.collect(1) == [1]
    assert solution.collect(2) == [2]


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
