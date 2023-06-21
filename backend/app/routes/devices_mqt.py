import logging
from asyncio import sleep
from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from asyncio_mqtt import Message

from app.common.config import engine, hub_id, mqtt_service
from app.models.devices_db import Device, DeviceStatus
from common.mqtt_service import MQTTHandlerProtocol, MQTTRouter
from common.types import DeviceType

router = MQTTRouter()


class DeviceProtocol(Protocol):
    async def __call__(self, device: Device, message: Message) -> None:  # noqa: U100
        pass


def device_parser() -> Callable[[DeviceProtocol], MQTTHandlerProtocol]:
    def device_parser_wrapper(function: DeviceProtocol) -> MQTTHandlerProtocol:
        async def device_parser_inner(message: Message) -> None:
            device_id: str = message.topic.value.partition("/")[2]
            device = await engine.find_one(
                Device,
                Device.device_id == device_id,
                Device.status == DeviceStatus.PAIRED,
            )
            if device is None:
                await mqtt_service.publish(f"pairing/cancel/{device_id}", hub_id)
            else:
                await function(device, message)

        return device_parser_inner

    return device_parser_wrapper


@router.route(f"{DeviceType.ECHO.value}/#", subscribe=False)
@device_parser()
async def handle_echo(device: Device, message: Message) -> None:
    device.mark_active()
    await engine.save(device)
    logging.info(message.payload)


async def expiry_cleaner() -> None:
    while True:  # noqa: WPS457
        if mqtt_service.client is None:
            await sleep(10)
            continue

        logging.info("Expired device purge in progress")

        async for device in engine.find(
            Device,
            Device.status != DeviceStatus.DEAD,
            Device.expiry < datetime.utcnow(),
        ):
            logging.info(f"Device {device.id}/{device.device_id} has been expired")
            await mqtt_service.publish(f"pairing/cancel/{device.device_id}", hub_id)
            await mqtt_service.client.unsubscribe(device.device_topic)
            device.status = DeviceStatus.DEAD
            await engine.save(device)

        await sleep(10)
