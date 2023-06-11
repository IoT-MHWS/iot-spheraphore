from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.config import engine
from app.models.cells_db import Cell
from app.routes import cells_mub


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await engine.configure_database(
        [Cell],
        update_existing_indexes=True,
    )

    yield

    pass


# noinspection PyTypeChecker
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cells_mub.router)
