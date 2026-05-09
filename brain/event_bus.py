"""Dashboard event bus scaffold."""

from collections.abc import Awaitable, Callable

from models import DashboardEvent

EventSubscriber = Callable[[DashboardEvent], Awaitable[None]]


class EventBus:
    """Publishes canonical DashboardEvents to subscribers."""

    def __init__(self) -> None:
        self._subscribers: list[EventSubscriber] = []

    def subscribe(self, subscriber: EventSubscriber) -> None:
        self._subscribers.append(subscriber)

    async def publish(self, event: DashboardEvent) -> None:
        # TODO(Person B): add durable event persistence and websocket fanout.
        for subscriber in self._subscribers:
            await subscriber(event)
