from enum import Enum, auto
from typing import Optional

from odmantic import EmbeddedModel, Model


class Subject(EmbeddedModel):
    x: int
    y: int
    subject_id: int


class ClimateMode(Enum):
    COOLING = auto()
    HEATING = auto()
    READY = auto()


class LightMode(Enum):
    ON = auto()
    OFF = auto()


class Cell(Model):
    x: int
    y: int

    temperature: Optional[float] = None
    climate_mode: Optional[ClimateMode] = None

    illumination: Optional[float] = None
    light_mode: Optional[LightMode] = None

    subjects: Optional[list[Subject]] = None
