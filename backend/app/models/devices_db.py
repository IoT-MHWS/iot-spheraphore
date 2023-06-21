from datetime import datetime, timedelta
from enum import Enum

from odmantic import Model

from common.types import DeviceType

MULTIPLIER: int = 1000


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
    expiry: datetime

    def mark_active(self) -> None:
        self.expiry = datetime.utcnow() + timedelta(seconds=self.interval * MULTIPLIER)

    @property
    def device_topic(self) -> str:
        return f"{self.device_type.value}/{self.device_id}"
