from os import getenv
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
from odmantic import AIOEngine

file_directory: Path = Path.cwd()

mongodb_url: str = getenv("MONGODB_URL", "mongodb://root:example@localhost:27017/")
client: AsyncIOMotorClient = AsyncIOMotorClient(mongodb_url)
engine: AIOEngine = AIOEngine(client=client, database="spheraphore")
