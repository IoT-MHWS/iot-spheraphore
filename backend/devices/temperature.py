import logging
from asyncio import run
from os import getenv

from asyncio_mqtt import Message

from common.types import DeviceType
from devices.base import Device

logging.basicConfig(level=logging.INFO)


class TemperatureSensor(Device):
    device_type = DeviceType.TEMPERATURE_SENSOR

    def __init__(self) -> None:
        super().__init__()
        self.temperature: float = 21.1
        self.delta: float = 0

    async def handle_cooling(self, _: Message) -> None:
        self.delta = -0.01

    async def handle_heating(self, _: Message) -> None:
        self.delta = 0.01

    async def handle_ready(self, _: Message) -> None:
        self.delta = 0

    def route_all(self) -> None:
        super().route_all()
        self.route(f"climate/cooling/{self.device_id}")(self.handle_cooling)
        self.route(f"climate/heating/{self.device_id}")(self.handle_heating)
        self.route(f"climate/ready/{self.device_id}")(self.handle_ready)

    async def send_events(self) -> None:
        self.temperature = await self.request_grpc(
            "GetAirTemperature",
            self.temperature,
            self.delta,
        )
        if self.hub_id is not None:
            logging.info(f"Sending temperature: {self.temperature}")
            await self.publish(f"temperature-sensor/{self.device_id}", self.temperature)


if __name__ == "__main__":
    mqtt_host: str = getenv("MOSQUITTO_HOST", "localhost")
    mqtt_service: TemperatureSensor = TemperatureSensor()
    mqtt_service.route_all()
    run(mqtt_service.run_durable(mqtt_host=mqtt_host))
