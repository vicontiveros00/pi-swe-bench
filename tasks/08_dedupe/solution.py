def dedupe(lst):
    seen = set()
    for x in lst:
        if x in seen:
            lst.remove(x)
        seen.add(x)
    return lst
