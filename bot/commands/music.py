import discord
from discord.ext import commands
import youtube_dl
from bot.utils.helpers import manage_queue, clear_queue

class MusicCommands:
    def __init__(self):
        self.bot = bot
        self.queue = []
        self.current_song = None

    async def join_voice_channel(self, ctx):
        # play music from the provided URL
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client is None:
                await channel.connect()
            elif ctx.voice_client.channel != channel:
                await ctx.voice_client.move_to(channel)
        else:
            await ctx.send("You must be in the voice channel")


    @commands.command(name="play")
    async def play(self, ctx, url):
        await self.join_voice_channel(ctx)

        # get info about the song
        ydl_opts = {'format': 'bestaudio/best'}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url. download=False)
            title = info.get('title', 'Unknown Title')
            length = info.get('length')
            self.current_song = f"{title}, [{length}]"

        # add song to the queue
        self.queue manage_queue(self.queue, 'add', url)
        await ctx.send(f"Added to queue: {self.current_song}")

        # if nothing is playing 
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)
    
    async def play_next(self, ctx):
        if self.queue:
            url = self.queue.pop(0)

            # get info about the song
            ydl_opts = {'format': 'bestaudio/best'}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url. download=False)
                title = info.get('title', 'Unknown Title')
                length = info.get('length')
                self.current_song = f"{title}, [{length}]"
                audio_url = info['url']

            # play the song
            source = await discord.FFmpegOpusAudio.from_probe(audio_url)
            ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctxx)))

            await ctx.send(f"Now playing: {self.current.song}")
        else:
            self.current_song = None
            await ctx.send("Queue is empty.")

    @commands.command(name="current")
    async def current(self, ctx):
        if self.current_song:
            await ctx.send(f"Currenty playing: {self.current_song}")
        else:
            await ctx.send("No song is currently playing.")

    async def stop(self, ctx):
        # Logic to stop the currently playing music
        pass

    async def skip(self, ctx):
        # Logic to skip the currently playing track
        pass

    async def queue(self, ctx, url):
        # Logic to add a track to the queue
        pass

    async def show_queue(self, ctx):
        # Logic to display the current queue
        pass