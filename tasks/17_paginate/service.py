from page_math import page_count, slice_bounds


def paginate(items, page, per_page):
    """Return a dict describing one page of `items`.

    {"items": [...], "page": p, "pages": total_pages, "total": n}
    Pages are 1-based. Out-of-range pages yield an empty item list but still
    report the correct total page count. per_page is assumed >= 1.
    """
    n = len(items)
    pages = page_count(n, per_page)
    start, end = slice_bounds(page, per_page)
    return {"items": items[start:end], "page": page, "pages": pages, "total": n}
