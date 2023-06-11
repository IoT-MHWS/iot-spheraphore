from asyncio import CancelledError, get_event_loop
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from asyncio_mqtt import Client
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.common.config import engine, mqtt_service
from app.models.cells_db import Cell
from app.routes import cells_mub


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await engine.configure_database(
        [Cell],
        update_existing_indexes=True,
    )

    async with Client("mosquitto") as mqtt_client:
        mqtt_service.setup(client=mqtt_client)

        loop = get_event_loop()
        task = loop.create_task(mqtt_service.listen())

        yield

        task.cancel()
        with suppress(CancelledError):
            await task


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
