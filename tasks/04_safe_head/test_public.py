import sys
import traceback

import solution


def run():
    assert solution.safe_head([]) is None


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
