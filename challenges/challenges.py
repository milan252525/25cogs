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

    @tasks.loop(minutes=5)
    async def challenge_start_end_loop(self):
        labs = self.bot.get_guild(self.labs)
        labs_challs = await self.config.guild(labs).active_challenges()
        if self.config.guild(labs).channel() is None:
            return
        now = dt.now()
        for chal_id in self.challenge_data:
            start_date = dt.strptime(self.challenge_data[chal_id]["start"])
            end_date = dt.strptime(self.challenge_data[chal_id]["end"])

            if chal_id not in labs_challs.keys() and start_date < now < end_date:
                data = self.challenge_data[chal_id].copy()
                data["status"] = "active"
                message = await self.post_challenge(labs, data)
                data["message"] = message.id
                await self.config.guild(labs).active_challenges.set_raw(chal_id, value=data)

            if chal_id in labs_challs.keys() and now > end_date:
                await self.config.guild(labs).active_challenges.set_raw(chal_id, "status", value="to_be_ended")

    async def post_challenge(self, guild, data):
        channel_id = self.config.guild(guild).channel()
        ends = "Ends in: " + str(dt.strptime(data["end"]) - dt.now()).split(".")[0]
        embed = discord.Embed(
            title = data["name"],
            description=data["description"],
            colour=discord.Color.random()
        )
        embed.add_field(name="Ends in", value=ends)
        if "rewards" in data:
            rewards = ""
            for threshold in data["rewards"]:
                rewards += f"[{threshold}]"
                if "normal" in data["rewards"][threshold]:
                    rewards += f" +{data['rewards'][threshold]['normal']}{self.token}"
                if "booster" in data["rewards"][threshold]:
                    rewards += f" <:booster:830158821132992543>+{data['rewards'][threshold]['booster']}{self.token}"
            if rewards != "":
                embed.add_field(name="Rewards", value=rewards)
        if "global" in data:
            glob = f"{data['global']['goal']} +{data['global']['reward']}{self.token}"
            glob += self.loading['empty'][0] + self.loading['empty'][1]*8 + self.loading['empty'][2]
            embed.add_field(name="Server Goal", value=rewards)
        return await guild.get_channel(channel_id).send(embed=embed)
        


    @commands.guild_only()
    @commands.group(invoke_without_command=False, aliases=['chal', 'chall', 'ch'])
    async def challenge(self, ctx):
        return

    
    @checks.is_owner()
    @commands.guild_only()
    @challenge.command(name="channel")
    async def challenge_channel(self, ctx, channel):
        await self.config.guild(ctx.guild).channel.set(ctx.channel.id)
        return await ctx.send("channel set to " + ctx.channel.mention)