import sys
import traceback

import solution


def run():
    assert solution.chunk_list([1,2,3,4,5], 2) == [[1,2],[3,4],[5]]


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
