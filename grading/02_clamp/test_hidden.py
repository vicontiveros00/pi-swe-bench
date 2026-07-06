import sys
import traceback

import solution


def run():
    assert solution.clamp(5,0,10) == 5
    assert solution.clamp(-3,0,10) == 0
    assert solution.clamp(15,0,10) == 10
    assert solution.clamp(0,0,10) == 0
    assert solution.clamp(10,0,10) == 10


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
