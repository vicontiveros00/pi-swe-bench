import sys
import traceback


def run():
    import service as S

    r = S.paginate(list(range(13)), 3, 5)
    assert r["pages"] == 3, r["pages"]
    assert r["items"] == [10, 11, 12]
    assert r["page"] == 3 and r["total"] == 13

    # exact multiple: 10 items / 5 -> exactly 2 pages, no phantom 3rd
    r = S.paginate(list(range(10)), 2, 5)
    assert r["pages"] == 2
    assert r["items"] == [5, 6, 7, 8, 9]

    # first page
    r = S.paginate(list(range(13)), 1, 5)
    assert r["items"] == [0, 1, 2, 3, 4] and r["pages"] == 3

    # out-of-range page: empty items, but page count still correct
    r = S.paginate(list(range(13)), 4, 5)
    assert r["items"] == [] and r["pages"] == 3

    # empty input -> zero pages, empty page
    r = S.paginate([], 1, 5)
    assert r["items"] == [] and r["pages"] == 0 and r["total"] == 0

    # single short page
    r = S.paginate([1, 2, 3], 1, 10)
    assert r["items"] == [1, 2, 3] and r["pages"] == 1


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
    print("PASS")
