import discord
from discord.ext import tasks
from redbot.core import commands, Config, checks
from redbot.core.data_manager import cog_data_path

import brawlstats
import asyncio
from datetime import datetime as dt
import json

class Challenges(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=25202025)
        default_member = {"tokens" : 0, "progress" : {}, }
        default_server = {"active_challenges" : {}, "channel" : None}
        self.config.register_member(**default_member)
        self.config.register_global(**default_server)
        self.labs = 401883208511389716
        self.bsconfig = None
        with open(str(cog_data_path(self)).replace("Challenges", r"CogManager/cogs/challenges/challenge_data.json")) as file:
            self.challenge_data = json.load(file)
        self.token = " token"#"🪙"
        self.loading = {
            "empty": ["<:blankleft:821065351907246201>", "<:blankmid:821065351294615552>", "<:blankright:821065351621115914>"],
            "full": ["<:loadleft:821065351726366761>", "<:loadmid:821065352061780048>", "<:loadright:821065351903182889>"]
        }
        self.challenge_start_end_loop.start()

    def cog_unload(self):
        self.challenge_start_end_loop.cancel()

    async def initialize(self):
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.Client(
            ofcbsapikey["api_key"], is_async=True)

    def get_bs_config(self):
        if self.bsconfig is None:
            self.bsconfig = Config.get_conf(None, identifier=5245652, cog_name="BrawlStarsCog")
        return self.bsconfig

    def labs_check(self, guild: discord.Guild):
        return guild.id == self.labs

    def time_left(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if hours <= 24:
            return "{}h {:02}m".format(int(hours), int(minutes))
        else:
            return f"{int(hours)//24}d {(int(hours)//24)%24}h"

    @tasks.loop(minutes=5)
    async def challenge_start_end_loop(self):
        labs = self.bot.get_guild(self.labs)
        labs_challs = await self.config.guild(labs).active_challenges()
        if labs_challs is None:
            await self.config.guild(labs).set_raw("active_challenges", value={})
        now = dt.now()
        for chal_id in self.challenge_data:
            start_date = dt.strptime(self.challenge_data[chal_id]["start"], "%d/%m/%y %H:%M")
            end_date = dt.strptime(self.challenge_data[chal_id]["end"], "%d/%m/%y %H:%M")

            if chal_id not in labs_challs.keys() and start_date < now < end_date:
                data = self.challenge_data[chal_id].copy()
                data["status"] = "active"
                message = await self.post_challenge(labs, data)
                data["message"] = message.id
                await self.config.guild(labs).set_raw("active_challenges", chal_id, value=data)

            if chal_id in labs_challs.keys() and now > end_date:
                await self.config.guild(labs).set_raw("active_challenges", chal_id, "status", value="to_be_ended")

    async def post_challenge(self, guild, data):
        channel_id = await self.config.guild(guild).channel()
        ends = self.time_left((dt.strptime(data["end"], "%d/%m/%y %H:%M") - dt.now()).total_seconds())
        embed = discord.Embed(
            title = data["name"],
            description=data["description"],
            colour=discord.Color.random()
        )
        embed.add_field(name="Time left", value=ends, inline=False)
        if "rewards" in data:
            rewards = ""
            for threshold in data["rewards"]:
                rewards += f"[{threshold}]"
                if "normal" in data["rewards"][threshold]:
                    rewards += f" +{data['rewards'][threshold]['normal']}{self.token}"
                if "booster" in data["rewards"][threshold]:
                    rewards += f" <:booster:830158821132992543>+{data['rewards'][threshold]['booster']}{self.token}"
                rewards += "\n"
            if rewards != "":
                embed.add_field(name="Rewards", value=rewards, inline=False)
        if "global" in data:
            glob_rew = f"[{data['global']['goal']}] +{data['global']['reward']}{self.token}"
            glob_pro= "0/{data['global']['goal']}\n" + self.loading['empty'][0] + self.loading['empty'][1]*8 + self.loading['empty'][2]
            embed.add_field(name="Server Goal", value=glob_rew, inline=False)
            embed.add_field(name="Progress", value=glob_pro, inline=False)
        return await guild.get_channel(channel_id).send(embed=embed)
        


    @commands.guild_only()
    @commands.group(invoke_without_command=False, aliases=['chal', 'chall', 'ch'])
    async def challenge(self, ctx):
        return

    
    @checks.is_owner()
    @commands.guild_only()
    @challenge.command(name="channel")
    async def challenge_channel(self, ctx, channel:discord.TextChannel):
        await self.config.guild(ctx.guild).channel.set(channel.id)
        return await ctx.send("channel set to " + channel.mention)