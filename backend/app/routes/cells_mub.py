from typing import Optional

from fastapi import APIRouter, HTTPException
from odmantic import ObjectId
from pydantic import BaseModel
from starlette.status import HTTP_404_NOT_FOUND

from app.common.config import engine
from app.models.cells_db import Cell, ClimateMode, LightMode, Subject
from common.types import DeviceType

router = APIRouter(prefix="/admin/cells")


class CellInput(BaseModel):
    x: int
    y: int


@router.post("")
async def create_cell(data: CellInput) -> Cell:
    cell: Cell = Cell(**data.dict())
    await engine.save(cell)
    return cell


class CellUpdate(BaseModel):
    temperature: Optional[float] = None
    climate_mode: Optional[ClimateMode] = None

    illumination: Optional[float] = None
    light_mode: Optional[LightMode] = None

    subjects: Optional[list[Subject]] = None

    devises: Optional[list[DeviceType]] = None


@router.put("/<cell_id>")
async def update_cell(data: CellUpdate, cell_id: ObjectId) -> Cell:
    cell = await engine.find_one(Cell, Cell.id == cell_id)
    if cell is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND)
    cell.update(data.dict())
    await engine.save(cell)
    return cell
