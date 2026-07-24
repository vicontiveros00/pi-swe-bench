# Tracks handlers per topic, preserving subscription order.

class Registry:
    def __init__(self):
        self._by_topic = {}   # topic -> list of (token, handler)
        self._next = 1

    def add(self, topic, handler):
        token = self._next
        self._next += 1
        self._by_topic.setdefault(topic, []).append((token, handler))
        return token

    def remove(self, token):
        # BUG: only removes from the FIRST topic that has a matching token and
        # then keeps scanning, but compares token to the handler tuple, so it
        # never actually matches -> nothing is ever removed.
        for topic, entries in self._by_topic.items():
            for e in entries:
                if e == token:
                    entries.remove(e)

    def handlers(self, topic):
        return [h for _, h in self._by_topic.get(topic, [])]
