from fastapi import APIRouter, HTTPException
from odmantic import ObjectId
from starlette.status import HTTP_404_NOT_FOUND

from app.common.config import engine
from app.models.cells_db import Cell

router = APIRouter(prefix="/api/cells", tags=["cells"])


@router.get("")
async def list_cells() -> list[Cell]:
    """
    Lists all available cells, sorted by coordinates

    - sorting: by coordinates (0 0) -> (0 1) -> (1 0) -> (1 1)
    - filtering: none
    """
    return await engine.find(Cell, sort=(Cell.y, Cell.x))


@router.put("/{cell_id}")
async def require_temperature(cell_id: ObjectId, temperature: int | None) -> None:
    cell = await engine.find_one(Cell, Cell.id == cell_id)
    if cell is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Cell not found")

    cell.required_temperature = temperature
    await engine.save(cell)
