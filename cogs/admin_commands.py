from discord.ext import commands
import discord
import json
from utils import check_valid_role, participant_parse, get_proper_name
from inhouse import inhouse_function, update_results
import re
from pathlib import Path
import settings
from datetime import datetime
import pytz

#https://gist.github.com/Rapptz/6706e1c8f23ac27c98cee4dd985c8120
THUMBSUP = "👍"

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

class admin_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot # sets the client variable so we can use it in cogs

    @commands.Cog.listener()
    async def on_ready(self):
        print('admin commands loaded')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.reply('~~white~~ admin privilege required, sorry virgin')

    @commands.command()
    @commands.has_any_role("Admin")
    async def setign(self, ctx, *args):
        if len(args)<2:
            await ctx.reply('ur a dumbass')
            return
        member_id = args[0][2:-1]
        player_ign = ' '.join(args[1:])
        with open(settings.idmapping_fn,'r') as f:
            idmapping = json.load(f)
        if member_id in idmapping.keys():
            response = "setting <@"+member_id+">'s ign to "+player_ign
        else:
            response = "player not found in existing database, initializing <@"+member_id+">'s ign to "+player_ign
        idmapping[member_id] = player_ign
        with open(settings.idmapping_fn,'w') as f:
            json.dump(idmapping,f,indent=4,ensure_ascii=False)
        await ctx.send(response, allowed_mentions = discord.AllowedMentions(users=False))

    @commands.command()
    @commands.has_any_role("Admin")
    async def setroles(self, ctx, *args):
        if len(args)<2:
            await ctx.reply('ur a dumbass')
            return
        with open(settings.rolepref_fn,'r') as f:
            roleprefdict = json.load(f)
        with open(settings.idmapping_fn,'r') as f:
            idmapping = json.load(f)
        member_id = None
        player_ign = None
        if '<@' == args[0][:2]:
            member_id = args[0][2:-1]
            if member_id in idmapping.keys():
                player_ign = idmapping[str(member_id)]
            else:
                await ctx.reply("<@"+member_id+"> isn't registered yet btw - either use ign directly or register first")
                return
        else: #direct ign assignment
            parsed_ign = get_proper_name(args[0])
            if parsed_ign in roleprefdict.keys():
                player_ign = parsed_ign
            else:
                await ctx.reply(args[0]+' not found in existing database')
                return
        newrolepref = check_valid_role(args[1])
        if newrolepref is None:
            await ctx.reply('check syntax, you fucked up somewhere')
            return
        if member_id in idmapping.keys() or player_ign in roleprefdict.keys():
            response = 'setting '+player_ign+' as '+newrolepref
        else:
            response = 'player not found in existing database, directly setting '+player_ign+' as '+newrolepref
        roleprefdict[player_ign] = newrolepref
        with open(settings.rolepref_fn,'w') as f:
            json.dump(roleprefdict,f,indent=4,ensure_ascii=False)
        if settings.ENABLE_GDRIVE:
            gfile = drive.CreateFile({'id': settings.fileID})
            #gfile = drive.CreateFile({'parents': [{'id': fileID2}]})
            # Read file and set it as the content of this instance.
            gfile.SetContentFile(settings.rolepref_fn)
            gfile.Upload() # Upload the file.
        await ctx.send(response, allowed_mentions = discord.AllowedMentions(users=False))

    @commands.command()
    @commands.has_any_role("Admin")
    async def idmapping(self, ctx):
        with open(settings.idmapping_fn,'r') as f:
            idmapping = json.load(f)
        response = ''.join(['<@'+x+'>: '+idmapping[x]+'\n' for x in idmapping.keys()])
        await ctx.send(response, allowed_mentions = discord.AllowedMentions(users=False))

    @commands.command()
    @commands.has_any_role("Admin")
    async def allrolepref(self, ctx):
        with open(settings.rolepref_fn,'r') as f:
            roleprefdict = json.load(f)
        response = ''.join([x+': '+roleprefdict[x]+'\n' for x in roleprefdict.keys()])
        await ctx.send("```"+response+"```", allowed_mentions = discord.AllowedMentions(users=False))

    @commands.command()
    @commands.has_any_role("Admin")
    async def startinhouse(self, ctx: commands.Context):
        message = await ctx.send(f"Trying to start an inhouse. Thumbs up to join.\nParticipants: 0")
        await message.add_reaction(THUMBSUP)

    @commands.command()
    @commands.has_any_role("Admin")
    async def inhouse(self, ctx, *, arg):
        with open(settings.idmapping_fn,'r') as f:
            idmapping = json.load(f)
        #first, convert discord IDs to summoner names
        id_starts = [s.start() for s in re.finditer('<@',arg)]
        id_ends = [s.start() for s in re.finditer('>',arg)]
        for i, idx in enumerate(zip(id_starts, id_ends)):
            member_id = arg[idx[0]+2:idx[1]]
            if member_id not in idmapping.keys():
                await ctx.reply('<@'+member_id+"> doesn't exist in the mapping")
                return
            player_ign = idmapping[member_id]
            arg = arg.replace('<@'+member_id+'>',player_ign)
        #then read as list
        participants = participant_parse(arg)
        response = 'Generating inhouse matchups for:\n'+str(participants)
        await ctx.send(response)
        matchups, messages = await self.bot.loop.run_in_executor(None, inhouse_function, participants)
        if matchups is not None:
            response2 = "```"+matchups[0]+"```"
            await ctx.send(response2)
        else:
            await ctx.reply(messages)

    @commands.command()
    @commands.has_any_role("Admin")
    async def results(self, ctx, *args):
        tournament_code = None
        known_ign = settings.default_ign
        full_stats = False
        if len(args):
            used_idx = []
            for i,x in enumerate(args):
                if x.lower() == '-full':
                    used_idx.append(i)
                    full_stats = True
                if '-' in x and len(x)>20:
                    used_idx.append(i)
                    tournament_code = x
            if len(args)>len(used_idx):
                #then the last arg is ign
                arg_arr = list(range(len(args)))
                for j in used_idx:
                    arg_arr.remove(j)
                ign_idx = arg_arr[0]
                known_ign = args[ign_idx]

        response = "Processing latest match (code: {})...".format(tournament_code)
        await ctx.send(response)
        response2 = await self.bot.loop.run_in_executor(None, update_results,tournament_code, known_ign, settings.OUT_DIR)
        inhouse_channel = self.bot.get_channel(settings.OUTPUT_CHANNEL_ID)
        selected_plots = ['ratings']
        if full_stats:
            selected_plots+= ['elo_history','rank_distribution','synergy','kryptonite']
        for fn in selected_plots:
            out_fn = str(Path(settings.OUT_DIR) / (fn+'.png'))
            await inhouse_channel.send(file=discord.File(out_fn))
        if full_stats:
            await inhouse_channel.send("```"+'\n'.join(response2)+"```")
        response3 = 'done, check <#'+str(settings.OUTPUT_CHANNEL_ID)+'>'
        await ctx.send(response3)

    @commands.command()
    async def adminhelp(self, ctx):
        message = [
            '!setign <discord_tag> <ign>: add player to idmapping',
            "!setroles <discord_tag OR ign> <tjmas or 5 digit number>: set player's inhouse role pref",
            '!idmapping: show idmapping',
            '!allrolepref: show all roleprefs',
            "!inhouse <up to 10 participants, comma separated>: participants can be discord tags, igns, or string tuple in form of ('ign','mmr,rolepref')",
            "!results <tourney_code> <known_ign> -full: all arguments optional, enter tourney code to pull match. known ign is a participant. '-full' to output all stats"
        ]
        await ctx.reply('\n'.join(message))

async def setup(bot: commands.Bot):
    await bot.add_cog(admin_commands(bot))

    @bot.event
    async def on_reaction_add(reaction, user):
        await handle_reaction(reaction)

    @bot.event
    async def on_reaction_remove(reaction, user):
        await handle_reaction(reaction)

    async def handle_reaction(reaction: discord.Reaction):
        message = reaction.message
        content = message.content
        minutes = (pytz.timezone('utc').localize(datetime.utcnow()) - message.created_at).total_seconds() / 60
        if minutes > 60:
            print('Old message. Not handling reactions anymore.')
            return
        if not content.startswith("Trying to start an inhouse"):
            return
        if not message.author.bot:
            return
        count = 0
        up_reaction = None
        for reaction in message.reactions:
            if reaction.emoji == THUMBSUP:
                up_reaction = reaction
                count = reaction.count - 1
                break
        assert up_reaction
        l1, l2, *extra = content.split('\n')
        # checking extra prevents us from pinging people over and over
        up_users = [x async for x in up_reaction.users() if not x.bot]
        parts = ', '.join([x.name for x in up_users])
        is_completed = count >= 10
        if is_completed:
            l2 = f'Complete: {parts}'
            if not extra:
                l2 += '\nPinging...'
                ping = [f'<@{x.id}>' for x in up_users]
                new_message = f"We have 10, come join the inhouse -- {''.join(ping)}"
                await message.reply(new_message)
        else:
            l2 = f'Participants: {count}'
        content = f"{l1}\n{l2}"
        if extra:
            content += f'\n{extra[0]}'
        await message.edit(content=content)
