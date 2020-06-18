import discord
from discord.ext import tasks
from redbot.core import commands, Config, checks

import brawlstats
import asyncio
from datetime import datetime


class Challenges(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=25202025)
        default_member = {'tokens' : 0, 'tracking' : False, 'lastBattleTime' : "20200101T010101.000Z", 'progress' : 0, 'plant' : None}
        self.config.register_member(**default_member)
        self.config.register_global(
            plants = 0,
            zombies = 0
        )
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
    @challenge.command(name="track")
    async def challenge_track(self, ctx, group: str = None):
        if not self.labs_check(ctx.guild):
            return await ctx.send("This can only be used in LA Brawl Stars server.")
        labs_mem = ctx.guild.get_role(576028728052809728)
        if labs_mem not in ctx.author.roles:
            return await ctx.send("Only LA members can participate!")
        bs_conf = self.get_bs_config()
        if (await bs_conf.user(ctx.author).tag()) is None:
            return await ctx.send("Save your tag using `/save` first!")
        if group is None:
            recommended = "Plants" if (await self.config.plants()) > (await self.config.zombies()) else "Zombies"
            return await ctx.send(f"Choose your side!\nTo play as a zombie (EMZ, Frank, Mortis) type `/ch track zombie`.\nTo play as plant (Sprout, Spike, Rosa) type `/ch track plant`\nRecommended group: {recommended}.")
        if group.lower() not in ("plant", "zombie"):
            return await ctx.send("That doesn't look like a valid option.\nOptions: `zombie`, `plant`")
        if not (await self.config.member(ctx.author).tracking()):
            await self.config.member(ctx.author).plant.set(option.lower() == "plant")
            await self.config.member(ctx.author).tracking.set(True)
            return await ctx.send(f"Challenge tracking enabled!\nChosen group: {option.title()}")
        else:
            return await ctx.send("Your progress is already being tracked! Group cannot be changed after registering.")

    @commands.guild_only()
    @challenge.command(name="stats")
    async def challenge_stats(self, ctx, member: discord.Member = None):
        member = ctx.author if member is None else member
        if not self.labs_check(ctx.guild):
            return await ctx.send("This can only be used in LA Brawl Stars server.")
        if not (await self.config.member(member).tracking()):
            return await ctx.send(f"**{member.display_name}** isn't participating yet! (`/ch track`)")
        await ctx.send("Group: " + "Plants" if await self.config.member(member).plant() else "Zombies")
        await ctx.send("Challenge progress: " + str(await self.config.member(member).progress()))
        await ctx.send("Time of last seen battle: " + str(datetime.strptime(await self.config.member(member).lastBattleTime(), '%Y%m%dT%H%M%S.%fZ')))
    

    #datetime.strptime(ev['startTime'], '%Y-%m-%dT%H:%M:%S.%fZ')

    #@tasks.loop(minutes=15)
    #async def battle_check(self):
    @commands.guild_only()
    @challenge.command(name="run")
    async def challenge_run(self, ctx):
        members = await self.config.all_members(self.bot.get_guild(self.labs))
        bs_conf = self.get_bs_config()
        for m in members:
            if members[m]['tracking']:
                group_plant = members[m]['plant']
                progress = 0
                user = self.bot.get_guild(self.labs).get_member(m)
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
                    b_time = datetime.strptime(battle['battleTime'], '%Y%m%dT%H%M%S.%fZ')
                    if b_time <= datetime.strptime(members[m]['lastBattleTime'], '%Y%m%dT%H%M%S.%fZ'):
                        break
                    player = None
                    if "teams" in battle['battle']:
                        for t in battle['battle']['teams']:
                            for p in t:
                                if p['tag'].replace("#", "") == tag.upper():
                                    player = p
                    else:
                        for p in battle['battle']['players']:
                            if p['tag'].replace("#", "") == tag.upper():
                                player = p
                    #CHALLENGE CONDITION HERE
                    if group_plant:
                        if player['brawler']['name'] in ("SPIKE", "ROSA", "SPROUT"):
                            progress += 1
                            await ctx.send(player)
                    else:
                        if player['brawler']['name'] in ("MORTIS", "FRANK", "EMZ"):
                            progress += 1
                            await ctx.send(player)
                
                await self.config.member(user).progress.set(members[m]['progress'] + progress)
                await self.config.member(user).lastBattleTime.set(log[0]['battleTime'])
