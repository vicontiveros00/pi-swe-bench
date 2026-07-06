import sys
import traceback

import solution


def run():
    assert solution.chunk_list([1,2,3,4,5],2) == [[1,2],[3,4],[5]]
    assert solution.chunk_list([1,2,3,4],2) == [[1,2],[3,4]]
    assert solution.chunk_list([1,2,3],1) == [[1],[2],[3]]
    assert solution.chunk_list([],3) == []
    assert solution.chunk_list([1,2,3,4,5,6,7],3) == [[1,2,3],[4,5,6],[7]]


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
