import asyncio

from asyncio_mqtt import Client, Message

from app.common.config import mqtt_host


async def main() -> None:
    async with Client(mqtt_host) as client:  # type: Client
        async with client.messages() as messages:
            await client.subscribe("test/get")
            print("Client subscribed to 'test/get'")
            async for message in messages:  # type: Message
                print(f"New message: {message.payload!r}, echoing to 'test/put'")
                await client.publish("test/put", message.payload)


if __name__ == "__main__":
    asyncio.run(main())
