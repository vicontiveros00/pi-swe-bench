from registry import Registry


class EventBus:
    def __init__(self):
        self._reg = Registry()

    def subscribe(self, topic, handler):
        return self._reg.add(topic, handler)

    def unsubscribe(self, token):
        self._reg.remove(token)

    def publish(self, topic, payload):
        results = []
        for h in self._reg.handlers(topic):
            results.append(h(payload))
        return results
