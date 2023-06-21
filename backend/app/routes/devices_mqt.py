import logging
from asyncio import sleep
from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from asyncio_mqtt import Message
from pydantic import parse_raw_as

from app.common.config import engine, hub_id, mqtt_service
from app.models.cells_db import Cell, ClimateMode, LightMode, Subject
from app.models.devices_db import Device, DeviceStatus
from common.mqtt_service import MQTTHandlerProtocol, MQTTRouter
from common.types import DeviceType

router = MQTTRouter()


class DeviceProtocol(Protocol):
    async def __call__(
        self,
        device: Device | None,  # noqa: U100
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
                await function(device, cell, message)
                if cell is not None:
                    await engine.save(cell)
                device.mark_active()
                await engine.save(device)

        return device_parser_inner

    return device_parser_wrapper


@router.route(f"{DeviceType.ECHO.value}/#", subscribe=False)
@device_parser()
async def handle_echo(_: Device, __: Cell, message: Message) -> None:
    logging.info(message.payload)


async def set_climate_mode(
    device: Device, cell: Cell, climate_mode: ClimateMode
) -> None:
    cell.climate_mode = climate_mode
    if climate_mode != ClimateMode.BROKEN:
        await mqtt_service.publish(
            f"climate/{climate_mode.value}/{device.device_id}", None
        )


@router.route(f"{DeviceType.TEMPERATURE_SENSOR.value}/#", subscribe=False)
@device_parser()
async def handle_temperature(device: Device, cell: Cell, message: Message) -> None:
    if not isinstance(message.payload, bytes):
        return
    try:
        value = float(message.payload.decode("utf-8"))
    except ValueError as e:
        logging.warning("Bad data for temperature", exc_info=e)

    cell.temperature = value
    if cell.required_temperature is None:
        await set_climate_mode(device, cell, ClimateMode.BROKEN)
    elif value > cell.required_temperature + 1:
        await set_climate_mode(device, cell, ClimateMode.COOLING)
    elif value < cell.required_temperature - 1:
        await set_climate_mode(device, cell, ClimateMode.HEATING)
    elif cell.required_temperature - 0.1 <= value <= cell.required_temperature + 0.1:
        await set_climate_mode(device, cell, ClimateMode.READY)


@router.route(f"{DeviceType.ILLUMINATION_SENSOR.value}/#", subscribe=False)
@device_parser()
async def handle_illumination(cell: Cell, message: Message) -> None:
    if not isinstance(message.payload, bytes):
        return
    try:
        value = float(message.payload.decode("utf-8"))
    except ValueError as e:
        logging.warning("Bad data for illumination", exc_info=e)

    cell.illumination = value
    if cell.illumination < 500:
        cell.light_mode = LightMode.ON
    else:
        cell.light_mode = LightMode.OFF


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

        await sleep(100)


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
