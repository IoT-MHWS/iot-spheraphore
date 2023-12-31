import logging
from asyncio import CancelledError, get_event_loop
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.common.config import engine, mqtt_host, mqtt_service
from app.models.cells_db import Cell
from app.models.devices_db import Device
from app.routes import cells_mub, cells_rst, devices_mqt, devices_rst

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await engine.configure_database(
        [Cell, Device],  # type: ignore
        update_existing_indexes=True,
    )

    loop = get_event_loop()
    tasks = [
        loop.create_task(mqtt_service.run_durable(mqtt_host=mqtt_host)),
        loop.create_task(devices_mqt.expiry_cleaner()),
        loop.create_task(devices_mqt.reconnect_devices()),
    ]

    yield

    for task in tasks:
        task.cancel()
        with suppress(CancelledError):
            await task


mqtt_service.include_router(devices_mqt.router)

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
app.include_router(devices_rst.router)


@app.post("/test/mosquitto", tags=["test"])
async def test_mosquitto(topic: str, payload: str) -> None:
    await mqtt_service.publish(topic, payload)
