import logging
from asyncio import TaskGroup, sleep
from typing import Any

from asyncio_mqtt import Message

from common.mqtt_service import MQTTService


class Device(MQTTService):
    sender_sleep_interval: float = 5

    async def pairing_scan_ready(self, _: Message) -> None:
        logging.info("Pairing scan, responding")
        await self.publish("pairing/ready", "")

    async def pairing_connect(self, _: Message) -> None:
        logging.info("Pairing start initiated, confirming")
        await self.publish("pairing/confirm", "")

    def route_all(self) -> None:
        self.route("pairing/scan")(self.pairing_scan_ready)  # type: ignore
        self.route("pairing/start")(self.pairing_connect)  # type: ignore

    async def send_events(self) -> None:
        raise NotImplementedError

    async def sender_loop(self) -> None:
        while True:  # noqa: WPS457
            await self.send_events()
            await sleep(self.sender_sleep_interval)

    async def listen(self, **subscribe_kwargs: Any) -> None:
        async with TaskGroup() as task_group:
            task_group.create_task(super().listen(**subscribe_kwargs))
            task_group.create_task(self.sender_loop())
