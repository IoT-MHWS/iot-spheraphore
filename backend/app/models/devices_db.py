from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from odmantic import Model, ObjectId

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

    cell_id: Optional[ObjectId] = None

    status: DeviceStatus
    expiry: datetime

    def mark_active(self) -> None:
        self.expiry = datetime.utcnow() + timedelta(seconds=self.interval * MULTIPLIER)

    @property
    def device_topic(self) -> str:
        return f"{self.device_type.value}/{self.device_id}"
