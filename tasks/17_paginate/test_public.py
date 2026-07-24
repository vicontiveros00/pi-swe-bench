import sys
import traceback


def run():
    import service as S
    r = S.paginate(list(range(13)), 3, 5)
    assert r["pages"] == 3
    assert r["items"] == [10, 11, 12]


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
