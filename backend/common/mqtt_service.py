import logging
from asyncio import sleep
from collections.abc import Callable
from typing import Any, Protocol

from asyncio_mqtt import Client, Message, MqttError
from asyncio_mqtt.types import PayloadType


class MQTTHandlerProtocol(Protocol):
    async def __call__(self, message: Message) -> None:  # noqa: U100
        pass


class MQTTRouter:
    def __init__(self) -> None:
        self.subscriptions: list[str] = []
        self.handlers: dict[str, MQTTHandlerProtocol] = {}

    def subscribe(self, topic: str) -> None:
        self.subscriptions.append(topic)

    def route(
        self,
        topic: str,
        subscribe: bool = True,
    ) -> Callable[[MQTTHandlerProtocol], None]:
        if subscribe:
            self.subscribe(topic)

        def route_wrapper(handler: MQTTHandlerProtocol) -> None:
            self.handlers[topic] = handler

        return route_wrapper


class MQTTService(MQTTRouter):
    def __init__(self) -> None:
        super().__init__()
        self.client: Client | None = None

    def include_router(self, router: MQTTRouter) -> None:
        self.subscriptions.extend(router.subscriptions)
        self.handlers.update(router.handlers)

    def setup(self, client: Client) -> None:
        self.client = client

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

    async def run_durable(
        self,
        mqtt_host: str,
        interval: int = 4,
        **subscribe_kwargs: Any,
    ) -> None:
        reconnecting: bool = False
        while True:
            try:
                async with Client(hostname=mqtt_host) as mqtt_client:
                    self.setup(client=mqtt_client)
                    if reconnecting:
                        reconnecting = False
                        logging.error("Reconnection successful")
                    await self.listen(**subscribe_kwargs)
            except MqttError:
                reconnecting = True
                logging.error(f"Connection lost. Reconnecting in {interval} seconds...")
                self.client = None
                await sleep(interval)

    async def publish(self, topic: str, payload: PayloadType, **kwargs: Any) -> None:
        if self.client is None:
            raise EnvironmentError("Client was not setup")
        await self.client.publish(topic, payload, **kwargs)
