from fastapi import APIRouter
from pydantic import BaseModel

from app.common.config import engine
from app.models.cells_db import Cell

router = APIRouter(prefix="/admin/cells")


class CellInput(BaseModel):
    x: int
    y: int


@router.post("")
async def create_cell(data: CellInput) -> Cell:
    cell: Cell = Cell(**data.dict())
    await engine.save(cell)
    return cell
