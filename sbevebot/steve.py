import discord
import os
import sys
import logging
import random

from dotenv import load_dotenv
from pathlib import Path
from discord import Intents
from typing import Any

def pp_size_function():
    size =  random.randrange(20)
    sizestr = "smol" if size >= 0 and size <= 10 else "yuge"
    return (size, sizestr)

class Config():
    def __init__(self, path: str) -> None:
        env_path = Path(path)
        load_dotenv(dotenv_path=env_path)
        self.token = os.getenv("TOKEN") or ""
        self.guild_name = os.getenv("GUILD") or ""
        self.loghandler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

    def __str__(self) -> str:
        return f"Token: {self.token}"

class SteveBot(discord.Client):
    __guild_count = 0

    def __init__(self, *, intents: Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.emoji_list = ['🍆', '🤏']

    async def on_ready(self):
        for _ in self.guilds:
            self.__guild_count = self.__guild_count + 1
        print(f"Logged as {self.user}, member of {self.__guild_count} guilds(s)")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.startswith("!ppsize"):
            size, sizestr = pp_size_function()
            msg = await message.reply(f"{size} cm , {sizestr}")
            if sizestr == 'smol':
                await msg.add_reaction(self.emoji_list[1])
            else:
                await msg.add_reaction(self.emoji_list[0])


if __name__ == "__main__":
    # Load configuration
    conf = Config(sys.argv[1])
    intents = discord.Intents.default()
    intents.message_content = True

    client = SteveBot(intents=intents)
    client.run(conf.token, log_handler=conf.loghandler)

