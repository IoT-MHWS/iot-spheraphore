import logging
from asyncio import run
from os import getenv

from asyncio_mqtt import Message
from asyncio_mqtt.types import PayloadType

from common.types import DeviceType
from devices.base import Device

logging.basicConfig(level=logging.INFO)


class EchoDevice(Device):
    device_type = DeviceType.ECHO

    def __init__(self) -> None:
        super().__init__()
        self.payload: PayloadType | None = None

    async def handle_echo(self, message: Message) -> None:
        self.payload = message.payload

    def route_all(self) -> None:
        super().route_all()
        self.route("test/get")(self.handle_echo)

    async def send_events(self) -> None:
        if self.payload is not None:
            await self.publish("test/put", self.payload)
            self.payload = None


if __name__ == "__main__":
    mqtt_host: str = getenv("MOSQUITTO_HOST", "localhost")
    mqtt_service: EchoDevice = EchoDevice()
    mqtt_service.route_all()
    run(mqtt_service.run_durable(mqtt_host=mqtt_host))
