import sys
import traceback

import solution


def run():
    assert solution.binary_search([1,3,5,7], 7) == 3


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
