from enum import Enum

from odmantic import Model


class DeviceStatus(str, Enum):
    READY = "ready"
    PAIRING = "pairing"
    PAIRED = "paired"
    DEAD = "dead"


class Device(Model):
    device_id: str
    status: DeviceStatus
