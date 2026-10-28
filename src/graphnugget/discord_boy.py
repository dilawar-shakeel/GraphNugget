"""Discord bot that only talks to its owner.

Exposes two async functions:
    read_message()      -> wait for the next message from the owner
    send_message(text)  -> send a message to the owner (DM)

The owner is DISCORD_OWNER_ID from .env, or the bot application's owner if unset.
"""

import asyncio
import os

import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # enable "Message Content Intent" in the developer portal
client = discord.Client(intents=intents)

_inbox: asyncio.Queue[str] = asyncio.Queue()
_owner_id: int | None = int(os.getenv("DISCORD_OWNER_ID", "0")) or None
_ready = asyncio.Event()


@client.event
async def on_ready() -> None:
    global _owner_id
    if _owner_id is None:
        app = await client.application_info()
        _owner_id = app.owner.id
    print(f"Discord bot live as {client.user}, owner id {_owner_id}")
    _ready.set()


@client.event
async def on_message(message: discord.Message) -> None:
    # Ignore everyone except the owner (and the bot itself).
    if message.author.id != _owner_id or message.author == client.user:
        return
    await _inbox.put(message.content)


async def read_message() -> str:
    """Wait until the owner sends a message and return its text."""
    await _ready.wait()
    return await _inbox.get()


async def send_message(text: str) -> None:
    """DM the owner. Long text is split to fit Discord's 2000 char limit."""
    await _ready.wait()
    user = await client.fetch_user(_owner_id)
    for i in range(0, len(text), 2000):
        await user.send(text[i : i + 2000])


async def start() -> None:
    """Connect the bot; runs until cancelled."""
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN is not set in .env")
    await client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(start())
