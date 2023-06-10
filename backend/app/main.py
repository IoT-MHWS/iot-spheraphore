from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.config import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await engine.configure_database(
        [],
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
