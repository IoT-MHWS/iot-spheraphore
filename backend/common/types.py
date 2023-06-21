from enum import Enum

from pydantic import BaseModel


class DeviceType(str, Enum):
    TEMPERATURE_SENSOR = "temperature-sensor"
    ILLUMINATION_SENSOR = "illumination-sensor"
    CAMERA = "camera"
    ECHO = "echo"


class DeviceInfo(BaseModel):
    id: str  # noqa: VNE003
    type: DeviceType  # noqa: VNE003
    interval: float
