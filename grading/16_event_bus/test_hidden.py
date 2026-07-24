import sys
import traceback


def run():
    import bus as B

    calls = []
    bus = B.EventBus()
    t1 = bus.subscribe("n", lambda p: calls.append(("a", p)) or "a")
    t2 = bus.subscribe("n", lambda p: calls.append(("b", p)) or "b")

    # order preserved, both fire
    assert bus.publish("n", 1) == ["a", "b"]
    assert calls == [("a", 1), ("b", 1)]

    # unsubscribe the FIRST; only the second may fire now
    calls.clear()
    bus.unsubscribe(t1)
    assert bus.publish("n", 2) == ["b"]
    assert calls == [("b", 2)]

    # unsubscribing an unknown/already-removed token is a harmless no-op
    bus.unsubscribe(t1)
    bus.unsubscribe(9999)
    assert bus.publish("n", 3) == ["b"]

    # topics are isolated; a token only removes its own handler
    bus2 = B.EventBus()
    x = bus2.subscribe("x", lambda p: "x")
    y = bus2.subscribe("y", lambda p: "y")
    bus2.unsubscribe(x)
    assert bus2.publish("x", 0) == []
    assert bus2.publish("y", 0) == ["y"]

    # re-subscribing after removal restores firing, in new subscription order
    z = bus.subscribe("n", lambda p: "c")
    assert bus.publish("n", 4) == ["b", "c"]


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
