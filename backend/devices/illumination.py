import logging
from asyncio import run
from os import getenv

from common.types import DeviceType
from devices.base import Device

logging.basicConfig(level=logging.INFO)


class IlluminationSensor(Device):
    device_type = DeviceType.ILLUMINATION_SENSOR

    def __init__(self) -> None:
        super().__init__()
        self.illumination: float = 21.1

    async def send_events(self) -> None:
        if self.hub_id is not None:
            logging.info(f"Sending temperature: {self.illumination}")
            await self.publish(
                f"illumination-sensor/{self.device_id}", self.illumination
            )


if __name__ == "__main__":
    mqtt_host: str = getenv("MOSQUITTO_HOST", "localhost")
    mqtt_service: IlluminationSensor = IlluminationSensor()
    mqtt_service.route_all()
    run(mqtt_service.run_durable(mqtt_host=mqtt_host))
