# bot.py
import os
import numpy as np
import itertools
import asyncio
from unidecode import unidecode
import warnings
warnings.filterwarnings("ignore")
from utils import is_orca_working
import discord
from discord.ext import commands, tasks
from . import settings

if settings.ENABLE_GDRIVE:
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)
    #do this once at the start to avoid timing out discord wait
    gfile = drive.CreateFile({'id': settings.fileID})
    #fileID2 = config['GDRIVE']['file_id2']
    #gfile = drive.CreateFile({'parents': [{'id': fileID2}]})
    # Read file and set it as the content of this instance.
    gfile.SetContentFile(settings.rolepref_fn)
    gfile.Upload() # Upload the file.

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix = "!", intents = intents)

async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != '__init__.py':
            # cut off the .py from the file name
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"Loaded Cog: {filename[:-3]}")

@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.name == settings.GUILD:
            break
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})\n'
    )
    change_status.start()

statuslist = itertools.cycle([
    discord.Game(name = 'with Ahrizona!'),
    discord.Game(name = 'Yuumi is a crime'),
    discord.Activity(type=discord.ActivityType.watching, name = 'capcorgi int'),
    discord.Activity(type=discord.ActivityType.listening, name = 'Bizyze'),
])

@tasks.loop(seconds=15)
async def change_status():
    await bot.change_presence(activity=next(statuslist))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel.type == discord.ChannelType(0):
        if message.channel.guild.id != int(settings.DISCORD_IDS['server']):
            return
    elif message.channel.type == discord.ChannelType(1):
        print(str(message.author)+' sent a DM lmao!')
        return

    #replies to other users
    if str(message.author.id) == settings.DISCORD_IDS['orca'] and is_orca_working() and np.random.rand()<0.25:
        response = 'shut up <@{}> go back to your wage cage'.format(settings.DISCORD_IDS['orca'])
        await message.channel.send(response)
    if str(message.author.id) == settings.DISCORD_IDS['jacob'] and np.random.rand()<0.05:
        response = 'Thank you for sharing, Jacob!'
        await message.channel.send(response)
    if any(x in unidecode(message.content.lower().replace(" ","")) for x in ['jew','j3w']):
        #https://github.com/Rapptz/discord.py/issues/390
        await message.add_reaction('<:{}>'.format(settings.DISCORD_IDS['rgrs_reaction']))

    #"normal" commands
    if message.content.lower() in ["i guess we're desperate","we're desperate"]:
        response = "<@{}> they're desperate - I assume there's a lobby of 4 that needs 1 warm body".format(settings.DISCORD_IDS['intel'])
        await message.channel.send(response)
    if message.content.lower() in ["im bored","i'm bored","i am bored"]:
        waging = is_orca_working()
        if waging:
            response = "<@{}> is in his wagecage right now but he can join discord and play flex or arams from work\n".format(settings.DISCORD_IDS['orca']) + \
            "Alternatively, consider playing some inhouses <:{}>".format(settings.DISCORD_IDS['orca_reaction'])
        else:
            response = '<@{}> time to give us content (you are not working right now)'.format(settings.DISCORD_IDS['orca'])
        await message.channel.send(response)

    #https://stackoverflow.com/questions/49331096/why-does-on-message-stop-commands-from-working
    await bot.process_commands(message)
#bot.run(TOKEN)
async def main():
    async with bot:
        await load_extensions()
        await bot.start(settings.TOKEN)

asyncio.run(main())
#https://stackoverflow.com/questions/71504627/runtimewarning-coroutine-botbase-load-extension-was-never-awaited-after-upd
