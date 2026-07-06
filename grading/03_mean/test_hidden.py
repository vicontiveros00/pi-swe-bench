import sys
import traceback

import solution


def run():
    assert solution.mean([1,2]) == 1.5
    assert solution.mean([2,2,2]) == 2
    assert abs(solution.mean([1,2,4]) - 7/3) < 1e-9
    assert solution.mean([10]) == 10


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
