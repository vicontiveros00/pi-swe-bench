from pricing import to_cents, apply_percent_off, format_money


class Cart:
    def __init__(self):
        self._items = []          # list of (name, unit_cents, qty)
        self._percent_off = 0

    def add(self, name, unit_price, qty=1):
        self._items.append((name, to_cents(unit_price), qty))

    def apply_coupon(self, percent):
        self._percent_off = percent

    def subtotal_cents(self):
        return sum(unit * qty for _, unit, qty in self._items)

    def total_cents(self):
        sub = self.subtotal_cents()
        if self._percent_off:
            return apply_percent_off(sub, self._percent_off)
        return sub

    def total(self):
        return format_money(self.total_cents())
