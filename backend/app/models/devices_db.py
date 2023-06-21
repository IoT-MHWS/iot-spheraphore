from enum import Enum

from odmantic import Model

from common.types import DeviceType


class DeviceStatus(str, Enum):
    READY = "ready"
    PAIRING = "pairing"
    PAIRED = "paired"
    DEAD = "dead"


class Device(Model):
    device_id: str
    device_type: DeviceType
    interval: float

    status: DeviceStatus
