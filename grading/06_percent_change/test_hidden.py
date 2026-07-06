import sys
import traceback

import solution


def run():
    assert solution.percent_change(100,150) == 50
    assert solution.percent_change(0,5) is None
    assert solution.percent_change(200,100) == -50


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
