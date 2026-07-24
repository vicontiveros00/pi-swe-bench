# Pure pagination arithmetic, shared by several services.

def page_count(total, per_page):
    # number of pages needed to show `total` items, `per_page` per page.
    # BUG: integer division floors, so a partial final page is lost
    # (13 items / 5 per page -> 2, but you need 3).
    return total // per_page


def slice_bounds(page, per_page):
    # (start, end) indices for a 1-based page number.
    start = (page - 1) * per_page
    return start, start + per_page
