import sys
import traceback

import solution


def run():
    assert solution.compare_versions("1.2.1", "1.2") == 1


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
