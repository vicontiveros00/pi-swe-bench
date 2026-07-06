import sys
import traceback

import solution


def run():
    assert solution.merge_intervals([[1,2],[2,3]]) == [[1,3]]
    assert solution.merge_intervals([[1,4],[2,3]]) == [[1,4]]
    assert solution.merge_intervals([[1,2],[3,4]]) == [[1,2],[3,4]]
    assert solution.merge_intervals([[3,4],[1,2],[2,3]]) == [[1,4]]
    assert solution.merge_intervals([]) == []


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
