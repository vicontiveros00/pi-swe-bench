import sys
import traceback


def run():
    import bus as B
    calls = []
    bus = B.EventBus()
    t1 = bus.subscribe("n", lambda p: calls.append("a") or "a")
    t2 = bus.subscribe("n", lambda p: calls.append("b") or "b")
    bus.unsubscribe(t1)
    assert bus.publish("n", 1) == ["b"]


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
