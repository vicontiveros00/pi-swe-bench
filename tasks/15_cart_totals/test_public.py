import sys
import traceback


def run():
    import cart as C
    c = C.Cart()
    c.add("widget", 19.99)
    c.apply_coupon(10)
    assert c.total_cents() == 1799


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
