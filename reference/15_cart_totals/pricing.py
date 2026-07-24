import math


def to_cents(dollars):
    return int(round(dollars * 100))


def apply_percent_off(cents, percent):
    # round the DISCOUNT half-up, then subtract, so the price is exact to the cent
    discount = math.floor(cents * percent / 100 + 0.5)
    return cents - discount


def format_money(cents):
    return "${:.2f}".format(cents / 100)
