from __future__ import annotations

class Broker():
    def __init__(self):
        self.subscribers = set()

    def attach(self,subscriber: Subscriber):
        self.subscribers.add(subscriber)

    def route(self, topic, message: str):
        for subscriber in self.subscribers:
            if topic in subscriber.sub.topics:
                subscriber.sub.receive(message)


class Publisher():
    def __init__(self, broker: Broker):
        self.broker = broker

    def publish(self, topic, message):
        return self.broker.route(topic, message)


class Subscriber():
    def __init__(self, topics:list[str], routes: dict):
        self.topics = topics
        self.routes = routes

    def receive(self, message):
        print("Subscriber received")
        callbacks = self.routes.get(message, [])
        for callback in callbacks:
            callback()


class GUI:
    def __init__(self, broker:Broker):
        self.pub = Publisher(broker)
        routes = {"live_started": [self._on_live_started]}
        self.sub = Subscriber(["backend"], routes)

    def _on_live_button_clicked(self, message: str):
        self.pub.publish("gui", "live_button_clicked")

    def _on_live_started(self):
        print("---live started received in gui -> change live to stop---")


class Backend:
    def __init__(self, broker: Broker):
        self.pub = Publisher(broker)
        routes = {"live_button_clicked": [self._on_live_requested]}
        self.sub = Subscriber(["gui"], routes)


    def _on_live_requested(self):
        print("---live started in backend---")
        self.pub.publish("backend", "live_started")




if __name__ == "__main__":

    broker = Broker()
    backend = Backend(broker)
    gui = GUI(broker)

    broker.attach(backend)
    broker.attach(gui)

    gui._on_live_button_clicked("START LIVE")


    print("Done")