import sys
import traceback

import solution


def run():
    l = solution.Ledger()
    l.deposit(100); l.deposit(50)
    l.undo()
    assert l.balance == 100


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
