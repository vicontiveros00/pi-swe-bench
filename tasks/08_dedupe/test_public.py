import sys
import traceback

import solution


def run():
    inp = [1,2,1,3,2]
    assert solution.dedupe(inp) == [1,2,3]
    assert inp == [1,2,1,3,2]


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
