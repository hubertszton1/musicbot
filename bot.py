import discord
from discord.ext import commands
import yt_dlp
import os
import sys
from dotenv import load_dotenv
import asyncio
from collections import deque  # Use deque for efficient queue management
from functools import lru_cache  # Dodaj cache dla wyników wyszukiwania
import time  # Dodano moduł do mierzenia czasu

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env/.env'))
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('COMMAND_PREFIX')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

queues = {}  # Store queues for each guild
ffmpeg_executable = "ffmpeg"  # Define FFmpeg executable path globally

def check_queue(ctx):
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        source, title = queues[ctx.guild.id].popleft()  # Use deque for efficient pop
        ctx.voice_client.play(source, after=lambda e: check_queue(ctx))
        asyncio.run_coroutine_threadsafe(ctx.send(f"Odtwarzanie: {title}"), bot.loop)

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} jest online!')

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("Musisz być na kanale głosowym!")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("Bot nie jest na kanale głosowym!")

# Cache dla wyników wyszukiwania (maksymalnie 128 wyników)
@lru_cache(maxsize=64)
def search_youtube(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'geo_bypass': True,
        'cachedir': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            return info['webpage_url'], info['title']
        except Exception:
            return None, None

async def search_youtube_async(query):
    """Asynchroniczne wyszukiwanie na YouTube za pomocą yt-dlp."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'geo_bypass': True,
        'cachedir': False,
    }
    try:
        def run_ydl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        info = await asyncio.to_thread(run_ydl)
        return info['webpage_url'], info['title']
    except Exception:
        return None, None

async def get_audio_source(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'geo_bypass': True,
        'quiet': True,
        'cachedir': False,
    }
    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
        audio_url = info['url']
        title = info['title']
        source = await discord.FFmpegOpusAudio.from_probe(audio_url, executable=ffmpeg_executable, 
                                                          before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
        return source, title

async def get_audio_source_async(url):
    """Asynchroniczne pobieranie źródła audio za pomocą yt-dlp."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'geo_bypass': True,
        'quiet': True,
        'cachedir': False,
    }
    try:
        def run_ydl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        info = await asyncio.to_thread(run_ydl)
        audio_url = info['url']
        title = info['title']
        source = await discord.FFmpegOpusAudio.from_probe(audio_url, executable=ffmpeg_executable, 
                                                          before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
        return source, title
    except Exception as e:
        print(f"Error fetching audio source: {e}")
        return None, None

@bot.command()
async def play(ctx, *, query: str):
    start_time = time.perf_counter()  # Rozpoczęcie pomiaru czasu

    if not ctx.voice_client:
        await ctx.invoke(join)

    # Wyszukiwanie lub użycie URL
    if query.startswith("https"):
        url, title = query, None
    else:
        url, title = await search_youtube_async(query)

    if not url:
        await ctx.send("Nie znaleziono wyników dla podanej frazy.")
        return
        
    # Przygotowanie źródła audio w tle
    source, title = await get_audio_source_async(url)
    if not source:
        await ctx.send("Wystąpił problem z przygotowaniem źródła audio.")
        return

    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = deque()  # Inicjalizacja kolejki dla serwera

    if ctx.voice_client.is_playing():
        queues[ctx.guild.id].append((source, title))
        elapsed_time = time.perf_counter() - start_time  # Obliczenie czasu
        await ctx.send(f"Dodano do kolejki: {title}")
        print(f"czas: {elapsed_time:.2f} sekundy")
    else:
        ctx.voice_client.play(source, after=lambda e: check_queue(ctx))
        elapsed_time = time.perf_counter() - start_time  # Obliczenie czasu
        await ctx.send(f'Odtwarzanie: {title}')
        print(f"czas: {elapsed_time:.2f} sekundy")

@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Zatrzymano muzykę.")
    else:
        await ctx.send("Aktualnie nic nie jest odtwarzane.")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Muzyka wstrzymana.")
    else:
        await ctx.send("Aktualnie nic nie jest odtwarzane")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Wznawianie muzyki.")
    else:
        await ctx.send("Muzyka nie jest wstrzymana!")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Pominięto utwór.")
    else:
        await ctx.send("Aktualnie nic nie jest odtwarzane.")

bot.run(TOKEN)
