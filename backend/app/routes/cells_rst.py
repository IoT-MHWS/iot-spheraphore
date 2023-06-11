from fastapi import APIRouter

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
