# bot.py
import os
import numpy as np
import json
import pandas as pd
import pickle
import dill
import itertools
import asyncio
from inhouse import *
import time
import datetime
ENABLE_GDRIVE = False

if ENABLE_GDRIVE:
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive

    gauth = GoogleAuth()           
    drive = GoogleDrive(gauth)

    fileID = '1wJbgZ_iM3rkuyobeBcEYE0GmEic0gBKL'

    #do this once at the start to avoid timing out discord wait
    gfile = drive.CreateFile({'id': fileID})
    #gfile = drive.CreateFile({'parents': [{'id': '1qsHAMxPfBQfeIfdX5tOiDUBL7FHJfhfV'}]})
    # Read file and set it as the content of this instance.
    gfile.SetContentFile('rolepref.json')
    gfile.Upload() # Upload the file.

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
#client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix = "!", intents = intents)

async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            # cut off the .py from the file name
            await bot.load_extension(f"cogs.{filename[:-3]}")

with open('idmapping.json','r') as f:
    idmapping = json.load(f)
print('inhouse role json file loaded!')

def prefix_cmd(message,cmd):
    return cmd in message.content[:len(cmd)]

def check_admin(message):
    is_admin = np.any([r.name=='Admin' for r in message.author.roles])
    return is_admin

def is_orca_working():
    now = datetime.datetime.now()
    shift_start = datetime.time(19,30,0,0)
    shift_end = datetime.time(8,0,0,0)
    #first half of shift
    waging = False
    if now.weekday() in [2,3,4]:
        if now.time()>=shift_start:
            waging = True
    #second half
    if now.weekday() in [3,4,5]:
        if now.time()<=shift_end:
            waging = True
    #every other sat
    ww = datetime.datetime.now().isocalendar().week
    if ww%2==0:
        if now.weekday() in [5]:
            if now.time()>=shift_start:
                waging=True
    if ww%2==1:
        if now.weekday() in [6]:
            if now.time()<=shift_end:
                waging=True
    return waging

@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.name == GUILD:
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

@tasks.loop(minutes=5)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    #replies to other users
    if str(message.author.id) =='167495804108406785' and is_orca_working() and np.random.rand()<0.25:
        response = 'shut up <@167495804108406785> go back to your wage cage'
        await message.channel.send(response)  
    if str(message.author.id) =='211679114208215040' and np.random.rand()<0.05:
        response = 'Thank you for sharing, Jacob!'
        await message.channel.send(response)

    #normal commands
    if message.content == '!help':
        response = 'todo'
        await message.channel.send(response)

    elif message.content == '!viewrolepref':
        with open('idmapping.json','r') as f:
            idmapping = json.load(f)
        if str(message.author.id) not in idmapping.keys():
            await message.channel.send('user not found, ask amery for help')
            return
        with open('rolepref.json','r') as f:
            roleprefdict = json.load(f)
        currrolepref = roleprefdict[idmapping[str(message.author.id)]]
        response = str(message.author)+' ('+idmapping[str(message.author.id)]+')\'s current role pref is '+currrolepref
        await message.channel.send(response)

    elif message.content in ["i guess we're desperate","we're desperate"]:
        response = "<@&755793996390989976> they're desperate - I assume there's a lobby of 4 that needs 1 warm body"
        await message.channel.send(response)  

    elif message.content in ["im bored","i'm bored","i am bored"]:
        waging = is_orca_working()
        if waging:
            response = '<@167495804108406785> is in his wagecage right now but he can join discord and play flex or arams from work'
        else:
            response = '<@167495804108406785> time to give us content (you are not working right now)'
        await message.channel.send(response)  

    elif message.content == ['!code','im a jew']:
        response = 'legacy code from scamming verizon lootboxes'
        await message.channel.send(response)  
        # proc = subprocess.Popen(["cat", "/etc/services"], stdout=subprocess.PIPE, shell=True)
        # (out, err) = proc.communicate()
        # print("program output:", out)

    elif prefix_cmd(message,'!changerolepref'):
        with open('idmapping.json','r') as f:
            idmapping = json.load(f)
        if str(message.author.id) not in idmapping.keys():
            await message.channel.send('user not found, ask amery for help. maybe be a good club member and play more inhouses.')
            return
        #check if input is valid
        try:
            newrolepref = message.content.split(' ')[1]
        except:
            await message.channel.send('no argument passed through')
            return

        if len(newrolepref)>5:
            await message.channel.send("input too long")
            return

        if newrolepref.isdigit():
            if len(newrolepref)==5:
                response = 'setting '+str(message.author)+' ('+idmapping[str(message.author.id)]+')\'s role pref to '+newrolepref
                await message.channel.send(response)
                with open('rolepref.json','r') as f:
                    roleprefdict = json.load(f)
                roleprefdict[idmapping[str(message.author.id)]] = newrolepref
                with open('rolepref.json','w') as f:
                    json.dump(roleprefdict,f,indent=4,ensure_ascii=False)
                if ENABLE_GDRIVE:
                    gfile = drive.CreateFile({'id': fileID})
                    #gfile = drive.CreateFile({'parents': [{'id': '1qsHAMxPfBQfeIfdX5tOiDUBL7FHJfhfV'}]})
                    # Read file and set it as the content of this instance.
                    gfile.SetContentFile('rolepref.json')
                    gfile.Upload() # Upload the file.
            else:
                await message.channel.send('numeric role pref must be 5 integers')
        else:
            if (np.all([x in 'tjmas' for x in newrolepref]) and len(newrolepref)==len(set(newrolepref))) or newrolepref=='f' : 
                response = 'setting '+str(message.author)+' ('+idmapping[str(message.author.id)]+')\'s role pref to '+newrolepref
                await message.channel.send(response)
                with open('rolepref.json','r') as f:
                    roleprefdict = json.load(f)
                roleprefdict[idmapping[str(message.author.id)]] = newrolepref
                with open('rolepref.json','w') as f:
                    json.dump(roleprefdict,f,indent=4,ensure_ascii=False)
                if ENABLE_GDRIVE:
                    gfile = drive.CreateFile({'id': fileID})
                    #gfile = drive.CreateFile({'parents': [{'id': '1qsHAMxPfBQfeIfdX5tOiDUBL7FHJfhfV'}]})
                    # Read file and set it as the content of this instance.
                    gfile.SetContentFile('rolepref.json')
                    gfile.Upload() # Upload the file.
            else:
                await message.channel.send('u fucked up try again')

    #moderator commands
    if prefix_cmd(message,'!inhouse'):
        if not check_admin(message):
            response = '~~white~~ admin privilege required, sorry virgin'
            await message.channel.send(response)
            return
        with open('idmapping.json','r') as f:
            idmapping = json.load(f)
        args = message.content[9:]
        participants = args.replace(' ','').split(',')
        for i,p in enumerate(participants):
            if '<@' in p:
                participant_id = p[2:-1]
                if participant_id in idmapping.keys():
                    participants[i] = idmapping[participant_id]
        #the above checking needs to be more robust
        response = 'Generating inhouse matchups for:\n'+str(participants)
        await message.channel.send(response)
        STORED_CHANNEL = message.channel
        matchups = await bot.loop.run_in_executor(None, inhouse_function, participants, STORED_CHANNEL)
        #response2 = 'Team 1: '+str(matchups[0])+'\nTeam 2: '+str(matchups[1])
        response2 = ''.join([x+'\n' for x in matchups])
        await message.channel.send(response2)

    if prefix_cmd(message,'!setplayerign'):    
        if not check_admin(message):
            response = '~~white~~ admin privilege required, sorry virgin'
            await message.channel.send(response)
            return
        #TODO: make sure the idmapping json is written to and saved (and read)
        args = message.content[13:].strip()
        member_id = args[args.find('<@')+2:args.find('>')]
        member_ign = args.split('>')[-1].strip()
        with open('idmapping.json','r') as f:
            idmapping = json.load(f)
        if member_id in idmapping.keys():
            idmapping[member_id] = member_ign
            with open('idmapping.json','w') as f:
                json.dump(idmapping,f,indent=4,ensure_ascii=False)
            response = "setting <@"+member_id+">'s ign to "+member_ign
        else:
            idmapping[member_id] = member_ign
            with open('idmapping.json','w') as f:
                json.dump(idmapping,f,indent=4,ensure_ascii=False)
            response = "player not found in existing database, initializing <@"+member_id+">'s ign to "+member_ign
        await message.channel.send(response, allowed_mentions = discord.AllowedMentions(users=False))
    
    if prefix_cmd(message,'!initializeroles'):
        if not check_admin(message):
            response = '~~white~~ admin privilege required, sorry virgin'
            await message.channel.send(response)
            return
        args = message.content[17:].strip()
        member_id = args[args.find('<@')+2:args.find('>')]
        member_role_pref = args.split('>')[-1].strip()
        with open('rolepref.json','r') as f:
            roleprefdict = json.load(f)
        with open('idmapping.json','r') as f:
            idmapping = json.load(f)
        if member_id in idmapping.keys():
            roleprefdict[idmapping[str(member_id)]] = member_role_pref
            with open('rolepref.json','w') as f:
                json.dump(roleprefdict,f,indent=4,ensure_ascii=False)
            if ENABLE_GDRIVE:
                gfile = drive.CreateFile({'id': fileID})
                #gfile = drive.CreateFile({'parents': [{'id': '1qsHAMxPfBQfeIfdX5tOiDUBL7FHJfhfV'}]})
                # Read file and set it as the content of this instance.
                gfile.SetContentFile('rolepref.json')
                gfile.Upload() # Upload the file.
            response = 'intialized '+idmapping[str(member_id)]+' as '+member_role_pref
        else:
            response = 'ensure discord id exists in mapping'
        await message.channel.send(response, allowed_mentions = discord.AllowedMentions(users=False))
    
    if message.content == '!idmapping':
        if not check_admin(message):
            response = '~~white~~ admin privilege required, sorry virgin'
            await message.channel.send(response)
            return
        with open('idmapping.json','r') as f:
            idmapping = json.load(f)
        response = ''.join(['<@'+x+'>: '+idmapping[x]+'\n' for x in idmapping.keys()])
        await message.channel.send(response, allowed_mentions = discord.AllowedMentions(users=False))

    if message.content == '!viewallrolepref':
        if not check_admin(message):
            response = '~~white~~ admin privilege required, sorry virgin'
            await message.channel.send(response)
            return
        with open('rolepref.json','r') as f:
            roleprefdict = json.load(f)
        response = ''.join([x+': '+roleprefdict[x]+'\n' for x in roleprefdict.keys()])
        await message.channel.send(response, allowed_mentions = discord.AllowedMentions(users=False))

#bot.run(TOKEN)
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

asyncio.run(main())
#https://stackoverflow.com/questions/71504627/runtimewarning-coroutine-botbase-load-extension-was-never-awaited-after-upd