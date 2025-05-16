import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('COMMAND_PREFIX')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
FFMPEG_OPTIONS = {'options': '-vn'}

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You are not in voice channel.")

@bot.command()
async def leave(ctx):
    if not ctx.voice_clients:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You are not in a voice channel.")
            return
@bot.command()
async def play(ctx, *, url):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You are not in a voice channel.")
            return

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        if url.startswith("http://") or url.startswith("https://"):
            info = ydl.extract_info(url, download=False)
        else:
            # Use ytsearch1: to get the first search result only
            info = ydl.extract_info(f"ytsearch1:{url}", download=False)
            info = info['entries'][0]  # Get the first result from the search

        url2 = info['url']

    source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
    ctx.voice_client.stop()
    ctx.voice_client.play(source)
    await ctx.send(f"Now playing: {info.get('title', 'Unknown Title')}")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("Playback stopped.")

bot.run(TOKEN)