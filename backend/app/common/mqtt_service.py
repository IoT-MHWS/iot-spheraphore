import logging
from collections.abc import Callable
from typing import Any, Protocol

from asyncio_mqtt import Client, Message
from asyncio_mqtt.types import PayloadType


class MQTTHandlerProtocol(Protocol):
    async def __call__(self, message: Message) -> None:  # noqa: U100
        pass


class MQTTService:
    def __init__(self) -> None:
        self.client: Client | None = None
        self.subscriptions: list[str] = []
        self.handlers: dict[str, MQTTHandlerProtocol] = {}

    def setup(self, client: Client) -> None:
        self.client = client

    def subscribe(self, topic: str) -> None:
        self.subscriptions.append(topic)

    def route(
        self, topic: str, subscribe: bool = False
    ) -> Callable[[MQTTHandlerProtocol], None]:
        if subscribe:
            self.subscribe(topic)

        def route_wrapper(handler: MQTTHandlerProtocol) -> None:
            self.handlers[topic] = handler

        return route_wrapper

    async def _handle_one(self, message: Message) -> None:
        for topic, handler in self.handlers.items():
            if message.topic.matches(topic):
                try:
                    await handler(message)
                except Exception as e:
                    logging.error(f"Handle for topic '{topic}' exited", exc_info=e)

    async def listen(self, **subscribe_kwargs: Any) -> None:
        if self.client is None:
            raise EnvironmentError("Client was not setup")
        async with self.client.messages() as messages:
            for subscription in self.subscriptions:
                await self.client.subscribe(subscription, **subscribe_kwargs)

            async for message in messages:
                await self._handle_one(message)

    async def publish(self, topic: str, payload: PayloadType, **kwargs: Any) -> None:
        if self.client is None:
            raise EnvironmentError("Client was not setup")
        await self.client.publish(topic, payload, **kwargs)
