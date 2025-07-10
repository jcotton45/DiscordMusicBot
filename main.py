import discord
from discord.ext import commands
import os
from music import Music
from helper import Helper
import requests
import json
bot_token = os.getenv("DISCORD_TOKEN")

client = commands.Bot(command_prefix='!', intents=discord.Intents.all())


@client.event
async def on_ready():
    print("Thicc bot ready")
    print("----------------")


@client.command()
async def hello(ctx):
    await ctx.send("Hello member")


@client.command()
async def goodbye(ctx):
    await ctx.send("goodbye")

@client.command()
async def joke(ctx):
    import requests

    joke_url = "https://jokes-always.p.rapidapi.com/erJoke"

    headers = {
        "X-RapidAPI-Key": joke_api,
        "X-RapidAPI-Host": "jokes-always.p.rapidapi.com"
    }

    response = requests.get(joke_url, headers=headers)

    channel = client.get_channel(1228908250435555381)
    await channel.send(response.json()['data'])




@client.event
async def on_member_join(member):
    channel = client.get_channel(1228908250435555381)
    await channel.send("Welcome to Dev Server")


@client.event
async def on_member_remove(member):
    channel = client.get_channel(1228908250435555381)
    await channel.send("Goodbye")


@client.command(pass_context=True)
async def join(ctx):
    if (ctx.author.voice):
        channel = ctx.message.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You are not in a voice channel!")


@client.command(pass_context=True)
async def leave(ctx):
    if (ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
        await ctx.send("bot has left the voice channel")
    else:
        await ctx.send("you are not in a voice channel")
        
async def load_cogs():
    await client.add_cog(Music(client))


async def setup_hook():
    await load_cogs()

client.setup_hook = setup_hook

client.run(bot_token)
