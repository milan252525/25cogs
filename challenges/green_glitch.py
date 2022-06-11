import discord
from discord.ext import tasks
from redbot.core import commands, Config, checks

import brawlstats
import asyncio
from datetime import datetime
from random import choice, shuffle


class Challenges(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=424242696942)
        default_member = {'tracking': False, 'lastBattleTime': "20200627T170000.000Z", 'entries': 0, 'streak': 0}
        self.config.register_member(**default_member)
        self.cmg = 401883208511389716
        self.bsconfig = None
        self.battle_check.start()

    def cog_unload(self):
        self.battle_check.cancel()

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

    def cmg_check(self, guild: discord.Guild):
        return guild.id == self.cmg

    @commands.guild_only()
    @commands.group(invoke_without_command=True, aliases=['glitch'])
    async def challenge(self, ctx):
        await ctx.send("Leaderboard: <#985294291305906196>")

    @commands.guild_only()
    @challenge.command(name="track")
    async def challenge_track(self, ctx):
        if await self.config.member(ctx.author).tracking():
            return await ctx.send("Your progress is already being tracked!")
        if not self.cmg_check(ctx.guild):
            return await ctx.send("This can only be used in CMG Brawl Stars server.")
        labs_mem = ctx.guild.get_role(576028728052809728)
        special = ctx.guild.get_role(706420605309812776)
        if labs_mem not in ctx.author.roles and special not in ctx.author.roles:
            return await ctx.send("Only CMG members can participate!")
        bs_conf = self.get_bs_config()
        if (await bs_conf.user(ctx.author).tag()) is None:
            return await ctx.send("Save your tag using `/save` first!")
        await self.config.member(ctx.author).tracking.set(True)
        return await ctx.send(f"Challenge tracking enabled!\n")

    @commands.guild_only()
    @challenge.command(name="stats")
    async def challenge_stats(self, ctx, member: discord.Member = None):
        member = ctx.author if member is None else member
        if not self.cmg_check(ctx.guild):
            return await ctx.send("This can only be used in CMG Brawl Stars server.")
        if not (await self.config.member(member).tracking()):
            return await ctx.send(f"**{member.display_name}** isn't participating yet! (`/glitch track`)")
        embed = discord.Embed(colour=discord.Colour.green(), title="Stats")
        embed.add_field(name="Current streak", value=await self.config.member(member).streak())
        embed.add_field(name="Total entries", value=await self.config.member(member).entries())
        embed.set_footer(
            text=f"Time of last seen battle:  {datetime.strptime(await self.config.member(member).lastBattleTime(), '%Y%m%dT%H%M%S.%fZ')}")
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.guild_only()
    @challenge.command(name="enable")
    async def challenge_enable(self, ctx):
        enabled = await self.config.enabled()
        await self.config.enabled.set(not enabled)
        await ctx.send(f"Challenge enabled: {not enabled}")

    @tasks.loop(minutes=15)
    async def battle_check(self):
        if await self.config.enabled():
            error_ch = self.bot.get_channel(722486276288282744)
            cmg = self.bot.get_guild(self.cmg)
            members = await self.config.all_members(cmg)
            bs_conf = self.get_bs_config()
            tags = await bs_conf.all_users()
            for m in members:
                if "tracking" not in members[m]:
                    continue
                if cmg.get_member(m) is None:
                    continue
                if members[m]['tracking']:
                    user = cmg.get_member(m)
                    if user is None:
                        await error_ch.send(m)
                        continue
                    tag = tags[user.id]['tag'].replace("o", "0").replace("O", "0")
                    try:
                        log = await self.ofcbsapi.get_battle_logs(tag)
                        await asyncio.sleep(0.1)
                        log = log.raw_data
                    except brawlstats.errors.RequestError as e:
                        await error_ch.send(str(e))
                        break
                    except Exception as e:
                        print(e)
                        await error_ch.send(str(e))
                        break
                    for battle in reversed(log):
                        try:
                            b_time = datetime.strptime(battle['battleTime'], '%Y%m%dT%H%M%S.%fZ')
                            if b_time <= datetime.strptime(members[m]['lastBattleTime'], '%Y%m%dT%H%M%S.%fZ'):
                                continue
                            if battle['battle']['mode'] == "bigGame":
                                continue
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
                            if player is None:
                                await error_ch.send(f"{m}\n```py\n{battle}```")
                                continue

                            win = True
                            if "result" in battle['battle'] and battle['battle']['result'] == "draw":
                                win = False
                            if "result" in battle['battle'] and battle['battle']['result'] != "victory":
                                win = False
                            if "rank" in battle['battle'] and battle['battle']['mode'] == "soloShowdown" and battle['battle']['rank'] > 4:
                                win = False
                            if "rank" in battle['battle'] and battle['battle']['mode'] != "soloShowdown" and battle['battle']['rank'] > 2:
                                win = False

                            streak = await self.config.member(user).streak()
                            if "trophies" not in player['brawler']:
                                continue
                            if win and player['brawler']['trophies'] >= 400 and battle['battle']['mode'] in ('brawlBall', 'gemGrab', 'bounty', 'siege', 'hotZone', 'heist'):
                                streak = streak + 1
                            elif win and (player['brawler']['trophies'] < 400 or battle['battle']['mode'] not in ('brawlBall', 'gemGrab', 'bounty', 'siege', 'hotZone', 'heist')):
                                streak = streak
                            else:
                                streak = 0

                            entries = await self.config.member(user).entries()
                            if streak >= 5:
                                streak = 0
                                entries = entries + 1
                                await self.config.member(user).entries.set(entries)
                            await self.config.member(user).streak.set(streak)

                        except Exception as e:
                            await error_ch.send(f"{m}\n```py\n{e}```")
                            await error_ch.send(f"{m}\n```py\n{battle}```")
                            continue
                        try:
                            await self.config.member(user).lastBattleTime.set(log[0]['battleTime'])
                        except Exception as e:
                            await error_ch.send(f"{m}\n```py\n{e}```")
                            continue
            members = await self.config.all_members(cmg)
            total = []
            for m in members:
                mem = cmg.get_member(m)
                if mem is None:
                    continue
                if members[m]['tracking']:
                    total.append((m, members[m]['entries']))

            total.sort(key=lambda x: x[1], reverse=True)
            msg = ""
            for t in total[:30]:
                mem = cmg.get_member(t[0])
                msg += f"`{t[1]}` {discord.utils.escape_markdown(mem.display_name)}\n"

            embed = discord.Embed(colour=discord.Colour.green(), title="Green Glitch Leaderboard")
            embed.add_field(name=f"Registered: {len(total)}", value=msg if msg != "" else "-")
            lbmsg = await (self.bot.get_channel(740676677822185533)).fetch_message(740808025173917717)
            await lbmsg.edit(embed=embed)
            
    @battle_check.before_loop
    async def before_battle_check(self):
        await asyncio.sleep(10)

    @commands.command()
    async def glitchwinner(self, ctx):

        if ctx.author.id not in (425260327425409028, 359131399132807178, 605132366406615051):
            return await ctx.send("Hands off.")

        names = []

        cmg = self.bot.get_guild(self.cmg)
        members = await self.config.all_members(cmg)
        for m in members:
            if "tracking" not in members[m]:
                continue
            if cmg.get_member(m) is None:
                continue
            if members[m]['tracking']:
                user = cmg.get_member(m)
                entries = await self.config.member(user).entries()
                if entries > 20:
                    entries = 20
                for i in range(entries):
                    names.append(f"{user.mention} ({str(user)})")

        shuffle(names)
        await ctx.send(choice(names))
