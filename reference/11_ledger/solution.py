class Ledger:
    def __init__(self):
        self.balance = 0
        self.history = []
    def deposit(self, amt):
        self.balance += amt
        self.history.append(amt)
    def undo(self):
        if self.history:
            last = self.history.pop()
            self.balance -= last
