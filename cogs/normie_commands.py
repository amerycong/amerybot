from discord.ext import commands
import discord
import json
from utils import check_valid_role, get_proper_name
from inhouse import get_player_stats
import settings
from pathlib import Path
#https://gist.github.com/Rapptz/6706e1c8f23ac27c98cee4dd985c8120


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

class normie_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot # sets the client variable so we can use it in cogs

    @commands.Cog.listener()
    async def on_ready(self):
        print('normie commands loaded')

    @commands.command()
    async def viewrolepref(self, ctx):
        with open(settings.idmapping_fn,'r') as f:
            idmapping = json.load(f)
        if str(ctx.author.id) not in idmapping.keys():
            await ctx.reply('user not found, ask amery for help')
            return
        with open(settings.rolepref_fn,'r') as f:
            roleprefdict = json.load(f)
        currrolepref = roleprefdict[idmapping[str(ctx.author.id)]]
        response = str(ctx.author)+' ('+idmapping[str(ctx.author.id)]+')\'s current role pref is '+currrolepref
        await ctx.reply(response)

    @commands.command()
    async def changerolepref(self, ctx, arg=None):
        if arg == None:
            await ctx.reply('hello? no input?')
            return
        with open(settings.idmapping_fn,'r') as f:
            idmapping = json.load(f)
        if str(ctx.author.id) not in idmapping.keys():
            await ctx.reply('user not found, ask amery for help. maybe be a good club member and play more inhouses.')
            return
        #check if input is valid
        newrolepref = check_valid_role(arg)
        if newrolepref is None:
            await ctx.reply('check syntax, you fucked up somewhere')
            return
        response = 'setting '+str(ctx.author)+' ('+idmapping[str(ctx.author.id)]+')\'s role pref to '+newrolepref
        await ctx.reply(response)
        with open(settings.rolepref_fn,'r') as f:
            roleprefdict = json.load(f)
        roleprefdict[idmapping[str(ctx.author.id)]] = newrolepref
        with open(settings.rolepref_fn,'w') as f:
            json.dump(roleprefdict,f,indent=4,ensure_ascii=False)
        if settings.ENABLE_GDRIVE:
            gfile = drive.CreateFile({'id': settings.fileID})
            #gfile = drive.CreateFile({'parents': [{'id': fileID2}]})
            # Read file and set it as the content of this instance.
            gfile.SetContentFile(settings.rolepref_fn)
            gfile.Upload() # Upload the file.

    @commands.command()
    async def viewprogress(self, ctx, *args):
        with open(settings.idmapping_fn,'r') as f:
            idmapping = json.load(f)
        with open(settings.rolepref_fn,'r') as f:
            roleprefdict = json.load(f)
        if args:
            if '<@' == args[0][:2]:
                member_id = args[0][2:-1]
                if member_id in idmapping.keys():
                    ign = idmapping[member_id]
                else:
                    await ctx.reply("<@"+member_id+"> isn't registered yet", allowed_mentions = discord.AllowedMentions(users=False))
                    return
            else:
                parsed_ign = get_proper_name(args[0])
                if parsed_ign in roleprefdict.keys():
                    ign = parsed_ign
                else:
                    await ctx.reply(args[0]+" isn't registered yet")
                    return
        else:
            if str(ctx.author.id) in idmapping.keys():
                ign = idmapping[str(ctx.author.id)]
            else:
                await ctx.reply("you're not registered so no data for you")
                return
        response = await self.bot.loop.run_in_executor(None, get_player_stats, ign, settings.OUT_DIR, str(ctx.author.id))
        out_fn = str(Path(settings.OUT_DIR) / ('elo_history_'+str(ctx.author.id)+'.png'))
        await ctx.reply(file=discord.File(out_fn))
        await ctx.reply("```"+"\n".join(response)+"```")

    @commands.command()
    async def bothelp(self, ctx):
        message = [
            '!viewrolepref: show your inhouse role preferences',
            '!changerolepref <tjmas or 5 digit number>: set your inhouse role pref',
            '!viewprogress <optional discord tag or ign>: shows MMR over time and champs winrates. defaults to your own.'
        ]
        await ctx.reply('\n'.join(message))

async def setup(bot):
    await bot.add_cog(normie_commands(bot))
