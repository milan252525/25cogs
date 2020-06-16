import discord
from discord.ext import tasks

import brawlstats
import asyncio
from datetime import datetime


class Challenges(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=25202025)
        default_member = {'tokens' : 0, 'tracking' : False, 'lastBattleTime' : 0, 'progress' : 0}
        self.config.register_member(**default_member)
        self.labs = 401883208511389716
        self.bsconfig = None

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

    @commands.guild_only()
    @commands.group(invoke_without_command=True, aliases=['chal', 'chall', 'ch'])
    async def challenge(self, ctx):
        if not self.labs_check(ctx.guild):
            return await ctx.send("This can only be used in LA Brawl Stars server.")
        await ctx.send("Some cool challenge info here.")

    @commands.guild_only()
    @clubs.command(name="track")
    async def challenge_track(self, ctx):
        if not self.labs_check(ctx.guild):
            return await ctx.send("This can only be used in LA Brawl Stars server.")
        labs_mem = guild.get_role(576028728052809728)
        if labs_mem not in ctx.author.roles:
            return await ctx.send("Only LA members can participate!")
        bs_conf = get_bs_config()
        if (await bs_conf.user(ctx.author).tag()) is None:
            return await ctx.send("Save your tag using `/save` first!")
        if not (await self.config.user(ctx.author).tracking()):
            await self.config.user(ctx.author).tracking.set(True)
            return await ctx.send("Challenge tracking enabled!")
        else:
            return await ctx.send("Your progress is already being tracked!")

    @commands.guild_only()
    @clubs.command(name="stats")
    async def challenge_stats(self, ctx):
        if not self.labs_check(ctx.guild):
            return await ctx.send("This can only be used in LA Brawl Stars server.")
        if not (await self.config.user(ctx.author).tracking()):
            return await ctx.send("Use `/challenge track` first!")
        await ctx.send(await self.config.user(ctx.author).progress())
        await ctx.send(await self.config.user(ctx.author).lastBattleTime())
    

    #datetime.strptime(ev['startTime'], '%Y-%m-%dT%H:%M:%S.%fZ')

    @tasks.loop(minutes=15)
    async def battle_check(self):
        members = await self.config.all_members(self.labs)
        bs_conf = get_bs_config()
        for m in members:
            if members[m]['tracking']:
                progress = 0
                user = self.bot.get_guild(self.labs).get_members(m)
                tag = await bs_conf.user(user).tag()
                try:
                    log = await self.ofcbsapi.get_battle_logs(tag)
                    log = log.raw_data
                except brawlstats.errors.RequestError:
                    break
                except Exception as e:
                    print(e)
                    break
                for battle in log:
                    b_time = datetime.strptime(battle['battle_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    if b_time <= datetime.strptime(members[m]['lastBattleTime'], '%Y-%m-%dT%H:%M:%S.%fZ'):
                        break
                    player = None
                    for t in battle['teams']:
                        for p in t:
                            if p['tag'].replace("#", "") == tag.upper():
                                player = p
                    #CHALLENGE CONDITION HERE
                    if p['brawlers']['name'] == "BARLEY":
                        progress += 1
                
                await self.config.member(user).progress.set(members[m]['progress'] + progress)
                await self.config.member(user).lastBattleTime.set(log[0]['battle_time'])