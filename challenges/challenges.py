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
        default_member = {'tracking' : False, 'lastBattleTime' : "20201116T080000.000Z", 'progress' : 0, 'pirate' : None, 'wins' : {}, 'loses' : {}}
        self.config.register_member(**default_member)
        self.config.register_global(
            pirates = 0,
            retro = 0,
            enabled = False
        )
        self.labs = 401883208511389716
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

    def labs_check(self, guild: discord.Guild):
        return guild.id == self.labs

    @commands.guild_only()
    @commands.group(invoke_without_command=True, aliases=['chal', 'chall', 'ch'])
    async def challenge(self, ctx):
        await ctx.send("Leaderboard: <#777231183926526013>")

    @commands.guild_only()
    @challenge.command(name="track")
    async def challenge_track(self, ctx, group: str = None):
        if not await self.config.enabled():
            return await ctx.send("Registering is currently disabled.")
        if await self.config.member(ctx.author).tracking():
            return await ctx.send("Your progress is already being tracked! Group cannot be changed after registering.")
        if not self.labs_check(ctx.guild):
            return await ctx.send("This can only be used in LA Brawl Stars server.")
        labs_mem = ctx.guild.get_role(576028728052809728)
        special = ctx.guild.get_role(706420605309812776)
        staff = ctx.guild.get_role(632198032607281162)
        if labs_mem not in ctx.author.roles and special not in ctx.author.roles and staff not in ctx.author.roles:
            return await ctx.send("Only LA members can participate!")
        bs_conf = self.get_bs_config()
        if (await bs_conf.user(ctx.author).tag()) is None:
            return await ctx.send("Save your tag using `/save` first!")
        if group is None:
            recommended = "Pirates" if (await self.config.pirates()) < (await self.config.retro()) else "Retro"
            return await ctx.send(f"Choose your side!\n**RECOMMENDED GROUP:** {recommended.title()}\nTo play as **Pirates** (Penny, Tick, Darryl) type `/ch track pirate`\nTo play as **Retropolis Trio** (Bull, Bibi, Crow) type `/ch track retro`")
        if group.lower() not in ("pirate", "retro"):
            return await ctx.send("That doesn't look like a valid option.\nOptions: `pirate`, `retro`")
        await self.config.member(ctx.author).pirate.set(group.lower() == "pirate")
        await self.config.member(ctx.author).tracking.set(True)
        if group.lower() == "pirate":
            await self.config.pirates.set(await self.config.pirates()+1)
        else:
            await self.config.retro.set(await self.config.retro()+1)
        return await ctx.send(f"Challenge tracking enabled!\nChosen group: {group.title()}")

    @commands.guild_only()
    @challenge.command(name="stats")
    async def challenge_stats(self, ctx, member: discord.Member = None):
        member = ctx.author if member is None else member
        if not self.labs_check(ctx.guild):
            return await ctx.send("This can only be used in LA Brawl Stars server.")
        if not (await self.config.member(member).tracking()):
            return await ctx.send(f"**{member.display_name}** isn't participating yet! (`/ch track`)")
        embed = discord.Embed(colour=discord.Colour.green(), title="Stats")
        embed.add_field(name="Group", value="Pirates" if await self.config.member(member).pirate() else "Retropolis Defenders")
        embed.add_field(name="Total wins", value=await self.config.member(member).progress())
        wins = await self.config.member(member).wins()
        loses = await self.config.member(member).loses()
        brawlers = ("PENNY", "TICK", "DARRYL") if await self.config.member(member).pirate() else ("BULL", "BIBI", "CROW")
        for br in brawlers:
            win = 0 if br not in wins else wins[br]
            loss = 0 if br not in loses else loses[br]
            if win + loss == 0:
                win_rate = 0
            else:
                win_rate = int((win / (win + loss)) * 100)
            embed.add_field(name=br.title(), value=f"{win} ({win_rate}%)")
        embed.set_footer(text=f"Time of last seen battle:  {datetime.strptime(await self.config.member(member).lastBattleTime(), '%Y%m%dT%H%M%S.%fZ')}")
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.guild_only()
    @challenge.command(name="enable")
    async def challenge_enable(self, ctx):
        enabled = await self.config.enabled()
        await self.config.enabled.set(not enabled)
        await ctx.send(f"Challenge enabled: {not enabled}")

    @tasks.loop(minutes=10)
    async def battle_check(self):
        if await self.config.enabled():
            error_ch = self.bot.get_channel(722486276288282744)
            labs = self.bot.get_guild(self.labs)
            members = await self.config.all_members(labs)
            bs_conf = self.get_bs_config()
            tags = await bs_conf.all_users()
            for m in members:
                if "tracking" not in members[m]:
                    continue
                if members[m]['tracking']:
                    group_pirate = members[m]['pirate']
                    progress = 0
                    user = labs.get_member(m)
                    if user is None:
                        continue
                    tag = tags[user.id]['tag'].replace("o", "0").replace("O", "0")
                    wins = members[m]['wins']
                    loses = members[m]['loses']
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
                    for battle in log:
                        try:
                            b_time = datetime.strptime(battle['battleTime'], '%Y%m%dT%H%M%S.%fZ')
                            if b_time <= datetime.strptime(members[m]['lastBattleTime'], '%Y%m%dT%H%M%S.%fZ'):
                                break
                         
                            if "id" in battle['event'] and battle['event']['id'] == 0 and ("type" not in battle['battle'] or battle['battle']['type'] != "ranked"):
                                continue
                            if "type" in battle['battle'] and battle['battle']['type'] == "friendly":
                                continue
                            if "result" in battle['battle'] and battle['battle']['result'] == "draw":
                                continue
                            if battle['battle']['mode'].lower().replace('-', '').replace(' ', '') in ('roborumble', 'biggame'):
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
                            #CHALLENGE CONDITION HERE

                            if "trophies" not in player['brawler']:
                                continue
                            if player['brawler']['trophies'] < 500:
                                continue

                            
                            
                         
                            win = True
                            if "result" in battle['battle'] and battle['battle']['result'] != "victory":
                                win = False
                            if "rank" in battle['battle'] and battle['battle']['mode'] == "soloShowdown" and battle['battle']['rank'] > 4:
                                win = False
                            if "rank" in battle['battle'] and battle['battle']['mode'] != "soloShowdown" and battle['battle']['rank'] > 2:
                                win = False
                            
                        
                            brawler_name = player['brawler']['name']
                            if group_pirate:
                                if brawler_name in ("PENNY", "TICK", "DARRYL"):
                                    if win:
                                        progress += 1
                                        if brawler_name in wins:
                                            wins[brawler_name] += 1
                                        else:
                                            wins[brawler_name] = 1
                                    else:
                                        if brawler_name in loses:
                                            loses[brawler_name] += 1
                                        else:
                                            loses[brawler_name] = 1
                            else:
                                if brawler_name in ("BULL", "BIBI", "CROW"):
                                    if win:
                                        progress += 1
                                        if brawler_name in wins:
                                            wins[brawler_name] += 1
                                        else:
                                            wins[brawler_name] = 1
                                    else:
                                        if brawler_name in loses:
                                            loses[brawler_name] += 1
                                        else:
                                            loses[brawler_name] = 1
                        except Exception as e:
                            await error_ch.send(f"{m}\n```py\n{e}```")
                            await error_ch.send(f"{m}\n```py\n{battle}```")
                            continue
                    
                    await self.config.member(user).progress.set(members[m]['progress'] + progress)
                    await self.config.member(user).set_raw('wins', value=wins)
                    await self.config.member(user).set_raw('loses', value=loses)
                    await self.config.member(user).lastBattleTime.set(log[0]['battleTime'])
            members = await self.config.all_members(labs)
            pirates = []
            pirates_total = 0
            retro = []
            retro_total = 0
            for m in members:
                if members[m]['tracking']:
                    if members[m]['pirate']:
                        pirates.append((m, members[m]['progress']))
                        pirates_total += members[m]['progress']
                    else:
                        retro.append((m, members[m]['progress']))
                        retro_total += members[m]['progress']
            pirates.sort(key=lambda x: x[1], reverse=True)
            retro.sort(key=lambda x: x[1], reverse=True)
            pirates_msg = ""
            for p in pirates[:15]:
                mem = labs.get_member(p[0])
                if mem is not None:
                    pirates_msg += f"`{p[1]}` {mem.display_name}\n"
            retro_msg = ""
            for z in retro[:15]:
                mem = labs.get_member(z[0])
                if mem is not None:
                    retro_msg += f"`{z[1]}` {mem.display_name}\n"

            embed = discord.Embed(colour=discord.Colour.purple(), title="Attack on Retropolis Leaderboard")
            embed.add_field(name=f"<:pirate_tick:776870272367853568> PIRATES Total: {pirates_total}", value=pirates_msg if pirates_msg != "" else "-", inline=False)
            embed.add_field(name=f"<:bull:664235934006378509> RETROPOLIS Total: {retro_total}", value=retro_msg if retro_msg != "" else "-")
            embed.set_footer(text=f"Pirates: {len(pirates)} Retropolis Defenders: {len(retro)}")
            lbmsg = await (self.bot.get_channel(777231183926526013)).fetch_message(777232421531025419)
            await lbmsg.edit(embed=embed)
