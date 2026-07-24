class Registry:
    def __init__(self):
        self._by_topic = {}
        self._next = 1

    def add(self, topic, handler):
        token = self._next
        self._next += 1
        self._by_topic.setdefault(topic, []).append((token, handler))
        return token

    def remove(self, token):
        for topic, entries in self._by_topic.items():
            self._by_topic[topic] = [(t, h) for (t, h) in entries if t != token]

    def handlers(self, topic):
        return [h for _, h in self._by_topic.get(topic, [])]
