import sys
import traceback

import solution


def run():
    assert solution.compare_versions("1.2.1","1.2") == 1
    assert solution.compare_versions("1.2","1.2.1") == -1
    assert solution.compare_versions("1.0","1") == 0
    assert solution.compare_versions("2.0","10.0") == -1
    assert solution.compare_versions("1.2.3","1.2.3") == 0


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
