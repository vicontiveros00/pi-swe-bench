def page_count(total, per_page):
    return (total + per_page - 1) // per_page


def slice_bounds(page, per_page):
    start = (page - 1) * per_page
    return start, start + per_page
