import asyncio
import os
import random
import openai

import discord
from discord.ext import commands
from fuzzywuzzy import fuzz
import yt_dlp

TOKEN = os.getenv('DISCORD_TOKEN')
openai.api_key = os.getenv('OPENAI_API_KEY')


async def download_video(query):
    mp3_file_path = f"mp3_files/{query}.mp3"
    if os.path.exists(mp3_file_path):
        print(f"Song '{query}' already exists. Skipping download.")
        return

    normalized_query = ' '.join(sorted(query.split()))
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'outtmpl': mp3_file_path,
        'duration': 900
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: ydl.download([f"ytsearch:{normalized_query}"]))

    print(f"Downloaded '{query}'.")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='', intents=intents)

@bot.event
async def on_ready():
    print('Bot is ready for use')
    print('--------------------')
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        for vc in bot.voice_clients:
            if not vc.is_playing() and not vc.is_paused():
                await vc.disconnect()

@bot.command()
async def hello(ctx):
    responses = ['hiya', 'hello there!', 'hola']
    await ctx.send(random.choice(responses))

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command()
async def thanks(ctx):
    responses = [
        "no problem! (´꒳`)",
        "you're welcome! (◕‿◕✿)",
        "anytime! (｡♥‿♥｡)",
        "no worries! (っ◕‿◕)っ",
        "glad i could help! (◠‿◠✿)"
    ]
    await ctx.send(random.choice(responses))

@bot.command()
async def skip(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("skipped, boop")
    else:
        await ctx.send("there is nothing playing...")

@bot.command()
async def play(ctx, *, query=None):
    if query is None:
        await ctx.send("play what?")
        return

    # Ensure the directory exists and then list the files
    mp3_directory = "mp3_files"
    if not os.path.exists(mp3_directory):
        os.makedirs(mp3_directory)  # Create the directory if it doesn't exist
    mp3_files = os.listdir(mp3_directory)

    normalized_query = ' '.join(sorted(query.split()))
    matching_scores = {}
    for mp3_file in mp3_files:
        normalized_mp3_file = ' '.join(sorted(mp3_file.replace(".mp3", "").split()))
        score = fuzz.token_set_ratio(normalized_query, normalized_mp3_file)
        matching_scores[mp3_file] = score

    if matching_scores:
        best_match = max(matching_scores, key=matching_scores.get)
        best_score = matching_scores[best_match]

        if best_score >= 70:  # Threshold for match score
            voice_channel = ctx.author.voice.channel
            if voice_channel:
                try:
                    await voice_channel.connect()
                except discord.ClientException:
                    pass
                ctx.voice_client.play(discord.FFmpegPCMAudio(f"{mp3_directory}/{best_match}"))
                await ctx.send(f"now playing '{best_match}' (matched with score: {best_score}).")
            else:
                await ctx.send("you need to be in a voice channel.")
            return

    await download_video(query)
    mp3_file_path = f"{mp3_directory}/{query}.mp3"
    if os.path.exists(mp3_file_path):
        voice_channel = ctx.author.voice.channel
        if voice_channel:
            try:
                await voice_channel.connect()
            except discord.ClientException:
                pass
            ctx.voice_client.play(discord.FFmpegPCMAudio(mp3_file_path))
            await ctx.send(f"now playing '{query}'.")
        else:
            await ctx.send("you need to be in a voice channel.")
    else:
        await ctx.send("Failed to download the song.")


@bot.command()
async def hanni(ctx, *, message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a cheerful and energetic anime girl who loves to help and chat with friends."},
                {"role": "user", "content": message}
            ]
        )

        bot_response = response['choices'][0]['message']['content']
        await ctx.send(bot_response)
    except KeyError:
        await ctx.send("An error occurred while processing the response.")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")



@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # Handle other types of errors or log them
        print(f"An error occurred: {error}")


if __name__ == '__main__':
    bot.run(TOKEN)
