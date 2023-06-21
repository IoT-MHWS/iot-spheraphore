import logging
from asyncio import TaskGroup, sleep
from typing import Any
from uuid import uuid4

from asyncio_mqtt import Message

from common.mqtt_service import MQTTService
from common.types import DeviceInfo, DeviceType
from common.utils import id_from_message


class Device(MQTTService):
    device_type: DeviceType
    sender_sleep_interval: float = 1

    def __init__(self) -> None:
        super().__init__()
        self.hub_id: str | None = None
        self.device_id: str = uuid4().hex

    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            id=self.device_id,
            type=self.device_type,
            interval=self.sender_sleep_interval,
        )

    async def pairing_scan_ready(self, message: Message) -> None:
        self.hub_id = id_from_message(message)
        if self.hub_id is None:
            return
        logging.info(f"Pairing scan from {self.hub_id}, responding")
        await self.publish(f"pairing/ready/{self.hub_id}", self.device_info().json())

    async def pairing_connect(self, message: Message) -> None:
        if self.hub_id is None or self.hub_id != id_from_message(message):
            return
        logging.info("Pairing start initiated, confirming")
        await self.publish(f"pairing/confirm/{self.hub_id}", self.device_id)

    async def pairing_cancel(self, message: Message) -> None:
        if self.hub_id is None or self.hub_id != id_from_message(message):
            return
        logging.warning(f"Pairing error from {self.hub_id}, cancelling")
        self.hub_id = None

    def route_all(self) -> None:
        self.route("pairing/scan")(self.pairing_scan_ready)
        self.route(f"pairing/start/{self.device_id}")(self.pairing_connect)
        self.route(f"pairing/cancel/{self.device_id}")(self.pairing_cancel)

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
