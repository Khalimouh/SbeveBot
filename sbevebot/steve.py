import discord
import os
import sys
import logging
import random
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
from pathlib import Path
from discord import Intents, Embed
from typing import Any
from ytmusicapi import YTMusic
from dataclasses import dataclass
from collections import deque

def pp_size_function():
    size =  random.randrange(20)
    sizestr = "smol" if size >= 0 and size <= 10 else "yuge"
    return (size, sizestr)

def checkSearchInput(msg):
    return len(msg.content) > 0 and isinstance(int(msg.content), int) and int(msg.content) <= 5 and int(msg.content) > 0


class Config():
    def __init__(self, path: str) -> None:
        env_path = Path(path)
        load_dotenv(dotenv_path=env_path)
        self.token = os.getenv("TOKEN") or ""
        self.guild_name = os.getenv("GUILD") or ""
        self.loghandler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

    def __str__(self) -> str:
        return f"Token: {self.token}"

@dataclass
class ytApiResult:
    titre: str
    duration: str
    videoId: str
    artist: str

class SteveBot(discord.Client):
    __guild_count = 0

    def __init__(self, *, intents: Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.emoji_list: list = ['🍆', '🤏']
        self.voice_channel: Any = None
        self.ytdl_options = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]}

        self.ffmpeg_before_options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        self.ffmpeg_options = '-vn'
        self.ytmusic = YTMusic("oauth.json", language='fr')

        self.song_queue = deque(maxlen=20)

    async def on_ready(self):
        for _ in self.guilds:
            self.__guild_count = self.__guild_count + 1
        print(f"Logged as {self.user}, member of {self.__guild_count} guilds(s)")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.startswith("#ppsize"):
            size, sizestr = pp_size_function()
            msg = await message.reply(f"{size} cm , {sizestr}")
            if sizestr == 'smol':
                await msg.add_reaction(self.emoji_list[1])
            else:
                await msg.add_reaction(self.emoji_list[0])
        if message.content.startswith("#join"):
            if message.author.voice and message.author.voice.channel:
                channel = message.author.voice.channel
                self.voice_channel = await channel.connect()
            else:
                await message.reply("You are not connected to a voice channel, retard !")
        if message.content.startswith("#leave"):
            if self.voice_channel:
                self.song_queue.clear()
                await self.voice_channel.disconnect()
                self.voice_channel = None
            else:
                await message.reply("You are not connected to a voice channel, retard !")

        if message.content.startswith("#qsize"):
            await message.reply(f"Queue size: {len(self.song_queue)}")

        if message.content.startswith("#stop"):
            if self.voice_channel.is_playing() or self.voice_channel.is_paused():
                self.voice_channel.stop()

        if message.content.startswith("#resume"):
            if self.voice_channel.is_paused():
                self.voice_channel.resume()

        if message.content.startswith("#pause"):
            if self.voice_channel.is_playing():
                self.voice_channel.pause()

        if message.content.startswith("#skip"):
            if self.voice_channel.is_playing():
                self.voice_channel.stop()
                await message.reply("Skipping this dogshit ass song...")
                self.__check_queue()

        if message.content.startswith("#search"):
            assert self.ytmusic
            if message.author.voice and message.author.voice.channel:
                if not self.voice_channel:
                    channel = message.author.voice.channel
                    self.voice_channel = await channel.connect()
            else:
                await message.reply("You are not connected to a voice channel, retard !")

            tokens = message.content.split(" ")

            if len(tokens) == 1:
                return await message.reply("My brother in christ, the fuck i'm i supposed to search  !")

            query = " ".join(tokens[1:])
            searchlist = self.ytmusic.search(query,filter="songs")

            #TODO: add multiple artists names
            marshalled_list = list(map(lambda x: ytApiResult(x["title"], x["duration"],x["videoId"], x["artists"][0]["name"]), searchlist))[:5]

            embed = Embed(
                title="Search results",
                description= "Select the song that should be played: ",
            )

            for pos, i in enumerate(marshalled_list):
                embed.add_field(name=pos + 1, value=f"{i.artist} - {i.titre} - {i.duration}", inline=False)

            await message.channel.send(embed=embed)

            msg: Any = None

            try:
                msg = await self.wait_for('message',check=checkSearchInput)
            except TimeoutError as e:
                print(e)


            selected_song= marshalled_list[int(msg.content) - 1 ]
            selected_song_id = selected_song.videoId


            if self.voice_channel.is_playing():
                self.song_queue.append(selected_song_id)
                await message.reply(f"Enqueued: {selected_song.artist} - {selected_song.titre} - {selected_song.duration}")
            else:
                await message.reply(f"Now playing: {selected_song.artist} - {selected_song.titre} - {selected_song.duration}")

            self.__play_song(selected_song_id)

        if message.content.startswith("#play"):
            if message.author.voice and message.author.voice.channel:
                if not self.voice_channel:
                    channel = message.author.voice.channel
                    self.voice_channel = await channel.connect()
            else:
                await message.reply("You are not connected to a voice channel, retard !")

            tokens = message.content.split(" ")

            if len(tokens) == 1:
                return await message.reply("My brother in christ, the fuck i'm i supposed to search  !")

            query = " ".join(tokens[1:])
            searchlist = self.ytmusic.search(query,filter="songs")

            marshalled_list = list(map(lambda x: ytApiResult(x["title"], x["duration"],x["videoId"], x["artists"][0]["name"]), searchlist))[0]

            selected_song= marshalled_list
            selected_song_id = selected_song.videoId

            if self.voice_channel.is_playing():
                self.song_queue.append(selected_song_id)
                await message.reply(f"Enqueued: {selected_song.artist} - {selected_song.titre} - {selected_song.duration}")
            else:
                await message.reply(f"Now playing: {selected_song.artist} - {selected_song.titre} - {selected_song.duration}")

            self.__play_song(selected_song_id)

    def __play_song(self, song_id: str):
        with YoutubeDL(self.ytdl_options) as yt:
            youtube_str = f'https://www.youtube.com/watch?v={song_id}'
            info = yt.extract_info(youtube_str, download=False)

        if info:
            try:
                self.voice_channel.play(discord.FFmpegOpusAudio(info["url"],options=self.ffmpeg_options, before_options=self.ffmpeg_before_options), after=lambda x=None: self.__check_queue())
            except TypeError as e:
                print(e)
        else:
            return

    def __check_queue(self):
        if len(self.song_queue) > 0:
            current_id = self.song_queue.popleft()
            self.__play_song(current_id)

if __name__ == "__main__":
    # Load configuration
    conf = Config(sys.argv[1])
    intents = discord.Intents.default()
    intents.message_content = True

    client = SteveBot(intents=intents)
    client.run(conf.token, log_handler=conf.loghandler)

