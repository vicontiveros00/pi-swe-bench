import sys
import traceback


def run():
    import cart as C

    # one item, 10% off: 1999c, discount 199.9 -> 200 (half-up) -> 1799
    c = C.Cart()
    c.add("widget", 19.99)
    c.apply_coupon(10)
    assert c.total_cents() == 1799, c.total_cents()
    assert c.total() == "$17.99"

    # no coupon -> exact subtotal
    c = C.Cart()
    c.add("a", 10.00, 2)
    c.add("b", 5.55)
    assert c.total_cents() == 2555

    # discount rounds half-up: 3333c * 15% = 499.95 -> 500 -> 2833
    c = C.Cart()
    c.add("x", 33.33)
    c.apply_coupon(15)
    assert c.total_cents() == 2833, c.total_cents()

    # 100% off is free; 0% off is a no-op
    c = C.Cart(); c.add("y", 12.34); c.apply_coupon(100)
    assert c.total_cents() == 0
    c = C.Cart(); c.add("z", 12.34); c.apply_coupon(0)
    assert c.total_cents() == 1234

    # exact-half boundary rounds up: 2000c * 25% = 500.0 -> 500 -> 1500
    c = C.Cart(); c.add("h", 20.00); c.apply_coupon(25)
    assert c.total_cents() == 1500

    # HALF-UP the DISCOUNT, not banker's and not "round the kept price".
    # $3.30 @ 25%: discount 82.5 -> half-up 83 -> total 247.
    # Banker's discount = 82 -> 248; rounding the kept price (247.5) -> 248 too.
    # So only rounding the DISCOUNT half-up yields 247.
    c = C.Cart(); c.add("hu1", 3.30); c.apply_coupon(25)
    assert c.total_cents() == 247, c.total_cents()

    # $10.10 @ 25%: discount 252.5 -> half-up 253 -> total 757
    # (banker's / price-rounding both give 758).
    c = C.Cart(); c.add("hu2", 10.10); c.apply_coupon(25)
    assert c.total_cents() == 757, c.total_cents()

    # quantities and coupon together: (1001*3)=3003, 33% -> 990.99 -> 991 -> 2012
    c = C.Cart(); c.add("q", 10.01, 3); c.apply_coupon(33)
    assert c.total_cents() == 2012, c.total_cents()


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
