import sys
import traceback

import solution


def run():
    assert solution.round_half_up(0.5) == 1
    assert solution.round_half_up(2.5) == 3


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
