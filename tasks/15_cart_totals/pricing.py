# Money is handled in integer cents everywhere to avoid float drift.

def to_cents(dollars):
    # dollars may be int or float like 19.99
    return int(round(dollars * 100))


def apply_percent_off(cents, percent):
    # percent is an int 0..100. Returns the DISCOUNTED price in cents.
    # BUG: truncates toward zero, and rounds the discount instead of the price,
    # so results drift by a cent on odd totals.
    discount = int(cents * percent / 100)
    return cents - discount


def format_money(cents):
    return "${:.2f}".format(cents / 100)
