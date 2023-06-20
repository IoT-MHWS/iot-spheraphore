import logging
from asyncio import CancelledError, get_event_loop
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from asyncio_mqtt import Message
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.common.config import engine, mqtt_host, mqtt_service
from app.models.cells_db import Cell
from app.routes import cells_mub, cells_rst


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await engine.configure_database(
        [Cell],
        update_existing_indexes=True,
    )

    loop = get_event_loop()
    task = loop.create_task(mqtt_service.run_durable(mqtt_host=mqtt_host))

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
app.include_router(cells_rst.router)


@mqtt_service.route("test/put", subscribe=True)
async def test_m(message: Message) -> None:
    logging.error(message.payload)


@app.post("/test/mosquitto", tags=["test"])
async def test_mosquitto(topic: str, payload: str) -> None:
    await mqtt_service.publish(topic, payload)
