from asyncio_mqtt import Message
from fastapi import APIRouter, HTTPException
from odmantic import ObjectId
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.common.config import engine, hub_id, mqtt_service
from app.models.devices_db import Device, DeviceStatus
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
    device_id = id_from_message(message)
    device = await engine.find_one(Device, Device.device_id == device_id)
    if device is None:
        device = Device(device_id=device_id, status=DeviceStatus.READY)
    elif device.status in {DeviceStatus.READY, DeviceStatus.DEAD}:
        device.status = DeviceStatus.READY
    await engine.save(device)


@router.put("/{device_id}/pair")
async def pair_device(device_id: ObjectId) -> None:
    device = await engine.find_one(Device, Device.id == device_id)

    if device is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND)
    if device.status != DeviceStatus.READY:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Wrong state")

    await mqtt_service.publish(f"pairing/start/{device.device_id}", hub_id)
    device.status = DeviceStatus.PAIRING
    await engine.save(device)


@mqtt_service.route(f"pairing/confirm/{hub_id}")
async def handle_pairing_confirm(message: Message) -> None:
    device_id = id_from_message(message)
    device = await engine.find_one(Device, Device.device_id == device_id)
    if device is None:
        await mqtt_service.publish(f"pairing/cancel/{device_id}", hub_id)
    else:
        device.status = DeviceStatus.PAIRED
        await engine.save(device)
