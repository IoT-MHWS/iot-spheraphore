import logging
from datetime import datetime, timedelta

from asyncio_mqtt import Message
from fastapi import APIRouter, HTTPException
from odmantic import ObjectId
from pydantic import ValidationError
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.common.config import engine, hub_id, mqtt_service
from app.models.cells_db import Cell
from app.models.devices_db import Device, DeviceStatus
from common.types import DeviceInfo
from common.utils import id_from_message

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("")
async def get_devices() -> list[Device]:
    return await engine.find(Device)


@router.post("/scan")
async def perform_device_scan() -> None:
    await mqtt_service.publish("pairing/scan", hub_id)


@mqtt_service.route(f"pairing/ready/{hub_id}")
async def handle_pairing_ready(message: Message) -> None:
    try:
        if isinstance(message.payload, (str, bytes)):
            device_info: DeviceInfo = DeviceInfo.parse_raw(message.payload)
        else:
            logging.warning("Wrong type for the ready message")
            return
    except ValidationError as e:
        logging.warning("Bad ready message received", exc_info=e)
        return

    device_data = {
        "device_id": device_info.id,
        "device_type": device_info.type,
        "interval": device_info.interval,
        "status": DeviceStatus.READY,
        "expiry": datetime.utcnow() + timedelta(minutes=1),
    }

    device = await engine.find_one(Device, Device.device_id == device_info.id)
    if device is None:
        device = Device(**device_data)  # type: ignore
    elif device.status in {DeviceStatus.READY, DeviceStatus.DEAD}:
        device.update(device_data)
    else:
        logging.warning(
            f"Paring error: device {device_info.id} already exists as {device.id}"
        )
        return
    await engine.save(device)


@router.put("/{device_id}/pair")
async def pair_device(device_id: ObjectId, cell_id: ObjectId) -> None:
    cell = await engine.find_one(Cell, Cell.id == cell_id)

    if cell is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Cell not found")

    device = await engine.find_one(Device, Device.id == device_id)

    if device is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Device not found")
    if device.status != DeviceStatus.READY:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Wrong state")

    cell.devices.append(device.device_type)
    device.cell_id = cell.id
    await engine.save(cell)

    await mqtt_service.publish(f"pairing/start/{device.device_id}", hub_id)
    device.status = DeviceStatus.PAIRING
    device.expiry = datetime.utcnow() + timedelta(minutes=1)
    await engine.save(device)


@mqtt_service.route(f"pairing/confirm/{hub_id}")
async def handle_pairing_confirm(message: Message) -> None:
    device_id = id_from_message(message)
    device = await engine.find_one(Device, Device.device_id == device_id)
    if device is None:
        await mqtt_service.publish(f"pairing/cancel/{device_id}", hub_id)
    else:
        if mqtt_service.client is not None:
            await mqtt_service.client.subscribe(device.device_topic)
        device.status = DeviceStatus.PAIRED
        device.mark_active()
        await engine.save(device)


async def unpair(device: Device) -> None:
    await mqtt_service.publish(f"pairing/cancel/{device.device_id}", hub_id)
    if mqtt_service.client is not None:
        await mqtt_service.client.unsubscribe(device.device_topic)
    device.status = DeviceStatus.DEAD
    await engine.save(device)


@router.delete("/{device_id}/pair")
async def unpair_device(device_id: ObjectId) -> None:
    device = await engine.find_one(Device, Device.id == device_id)

    if device is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND)
    if device.status != DeviceStatus.PAIRED:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Wrong state")

    await unpair(device)


@router.delete("/{device_id}")
async def remove_device(device_id: ObjectId) -> None:
    device = await engine.find_one(Device, Device.id == device_id)
    if device is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND)
    if device.status == DeviceStatus.PAIRED:
        await unpair(device)
    await engine.remove(Device, Device.id == device_id)
