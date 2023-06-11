from enum import Enum
from typing import Optional

from odmantic import EmbeddedModel, Model


class Subject(EmbeddedModel):
    x: int
    y: int
    subject_id: int


class ClimateMode(str, Enum):
    BROKEN = "broken"
    COOLING = "cooling"
    HEATING = "heating"
    READY = "ready"


class LightMode(str, Enum):
    ON = "on"
    OFF = "off"


class Cell(Model):
    x: int
    y: int

    temperature: Optional[float] = None
    climate_mode: Optional[ClimateMode] = None

    illumination: Optional[float] = None
    light_mode: Optional[LightMode] = None

    subjects: Optional[list[Subject]] = None
