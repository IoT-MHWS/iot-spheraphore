from os import getenv
from pathlib import Path
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
from odmantic import AIOEngine

from common.mqtt_service import MQTTService

file_directory: Path = Path.cwd()

mongodb_url: str = getenv("MONGODB_URL", "mongodb://root:example@localhost:27017/")
client: AsyncIOMotorClient = AsyncIOMotorClient(mongodb_url)
engine: AIOEngine = AIOEngine(client=client, database="spheraphore")

mqtt_host: str = getenv("MOSQUITTO_HOST", "localhost")
mqtt_service: MQTTService = MQTTService()

hub_id: str = uuid4().hex
