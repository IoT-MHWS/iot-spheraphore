from asyncio_mqtt import Message


def id_from_message(message: Message) -> str:
    if isinstance(message.payload, bytes):
        return message.payload.decode("utf-8")
    return str(message.payload)
