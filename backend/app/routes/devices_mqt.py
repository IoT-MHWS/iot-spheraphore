import logging
from asyncio import sleep
from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from asyncio_mqtt import Message
from pydantic import parse_raw_as

from app.common.config import engine, hub_id, mqtt_service
from app.models.cells_db import Cell, Subject
from app.models.devices_db import Device, DeviceStatus
from common.mqtt_service import MQTTHandlerProtocol, MQTTRouter
from common.types import DeviceType

router = MQTTRouter()


class DeviceProtocol(Protocol):
    async def __call__(
        self,
        cell: Cell | None,  # noqa: U100
        message: Message,  # noqa: U100
    ) -> None:
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
                cell = await engine.find_one(Cell, Cell.id == device.cell_id)
                await function(cell, message)
                if cell is not None:
                    await engine.save(cell)
                device.mark_active()
                await engine.save(device)

        return device_parser_inner

    return device_parser_wrapper


@router.route(f"{DeviceType.ECHO.value}/#", subscribe=False)
@device_parser()
async def handle_echo(_: Cell, message: Message) -> None:
    logging.info(message.payload)


@router.route(f"{DeviceType.TEMPERATURE_SENSOR.value}/#", subscribe=False)
@device_parser()
async def handle_temperature(cell: Cell, message: Message) -> None:
    if not isinstance(message.payload, float):
        return

    cell.temperature = message.payload


@router.route(f"{DeviceType.ILLUMINATION_SENSOR.value}/#", subscribe=False)
@device_parser()
async def handle_illumination(cell: Cell, message: Message) -> None:
    if not isinstance(message.payload, float):
        return

    cell.illumination = message.payload


@router.route(f"{DeviceType.CAMERA.value}/#", subscribe=False)
@device_parser()
async def handle_camera(cell: Cell, message: Message) -> None:
    if not isinstance(message.payload, (bytes, str)):
        return

    cell.subjects = parse_raw_as(list[Subject], message.payload)


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


async def reconnect_devices() -> None:
    while True:
        if mqtt_service.client is not None:
            break
        await sleep(10)

    async for device in engine.find(
        Device,
        Device.status == DeviceStatus.PAIRED,
        Device.expiry >= datetime.utcnow(),
    ):
        await mqtt_service.client.subscribe(device.device_topic)
        device.mark_active()
        await engine.save(device)
        logging.info(f"Device {device.id}/{device.device_id} reconnected successfully")
