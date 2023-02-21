import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.embed import randomize_colour
from redbot.core.utils.menus import menu, prev_page, next_page
from discord.ext import tasks

from .utils import *
from . import player_stats, game_stats

from random import choice
import asyncio
import brawlstats
from typing import Union
from re import sub
import datetime
import aiohttp
from cachetools import TTLCache
from operator import itemgetter, attrgetter
import pycountry
import math

class BrawlStarsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=5245652)
        default_user = {"tag": None, "alt": None, "name" : "", "altname" : "", "plsolo" : None, "plteam" : None, "lastsolo" : 0, "lastteam" : 0}
        self.config.register_user(**default_user)
        default_guild = {"clubs": {}}
        self.config.register_guild(**default_guild)
        self.maps = None
        self.icons = None
        self.aiohttp_session = aiohttp.ClientSession()

    async def initialize(self):
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError(
                "The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.Client(
            ofcbsapikey["api_key"], is_async=True)
        self.ofcbsapi.cache = TTLCache(10000, 60*10)
        self.starlist_key = (await self.bot.get_shared_api_tokens("starlist"))["starlist"]
        
    async def starlist_request(self, url):
        #"Authorization": f"Bearer {self.starlist_key}", 
        header = {"User-Agent": "CMG_bot"}
        async with self.aiohttp_session.get(url, headers=header) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                return {'status': str(resp.status) + " " + resp.reason}
            
    @commands.command(aliases=['bssave'])
    async def save(self, ctx, tag, member: discord.Member = None):
        """Save your Brawl Stars player tag"""
        member = ctx.author if member is None else member

        tag = tag.lower().replace('o', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        try:
            player = await self.ofcbsapi.get_player(tag)
            await self.config.user(member).tag.set(tag.replace("#", ""))
            await self.config.user(member).name.set(player.name)
            await ctx.send(embed=goodEmbed(f"BS account {player.name} was saved to {member.name}"))

        except brawlstats.errors.NotFoundError:
            await ctx.send(embed=badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            await ctx.send("**Something went wrong, please send a personal message to Modmail bot or try again!****")

    @commands.command(aliases=['bssave2'])
    async def savealt(self, ctx, tag, member: discord.Member = None):
        """Save your second Brawl Stars player tag"""
        member = ctx.author if member is None else member

        tag = tag.lower().replace('o', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        try:
            player = await self.ofcbsapi.get_player(tag)
            await self.config.user(member).alt.set(tag.replace("#", ""))
            await self.config.user(member).altname.set(player.name)
            await ctx.send(embed=goodEmbed(f"BS account {player.name} was saved to {member.name}"))

        except brawlstats.errors.NotFoundError:
            await ctx.send(embed=badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            await ctx.send("**Something went wrong, please send a personal message to Modmail bot or try again!****")

    @commands.has_permissions(administrator = True)
    @commands.command(aliases=['bsunsave'])
    async def unsave(self, ctx, member: discord.Member):
        await self.config.user(member).clear()
        await ctx.send("Done.")
            
    @commands.command(aliases=['rbs'])
    async def renamebs(self, ctx, member: discord.Member = None, club_name:bool = True):
        """Change a name of a user to be nickname|club_name"""
        await ctx.trigger_typing()
        prefix = ctx.prefix
        member = ctx.author if member is None else member
        
        if ctx.author != member and ctx.author.top_role < member.top_role:
            return await ctx.send("You can't do this!")

        tag = await self.config.user(member).tag()
        if tag is None:
            return await ctx.send(embed=badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))

        player = await self.ofcbsapi.get_player(tag)
        if "name" in player.raw_data["club"] and club_name:
            nick = f"{player.name} | {player.club.name}"
        else:
            nick = f"{player.name}"
        try:
            await member.edit(nick=nick[:31])
            await ctx.send(f"Done! New nickname: `{nick[:31]}`")
        except discord.Forbidden:
            await ctx.send(f"I dont have permission to change nickname of this user!")
        except Exception as e:
            await ctx.send(f"Something went wrong: {str(e)}")

    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(aliases=['p', 'bsp'])
    async def profile(self, ctx, *, member: Union[discord.Member, str] = None):
        """View player's BS statistics"""
        await ctx.trigger_typing()
        member = ctx.author if member is None else member
        embed = await player_stats.get_profile_embed(self.bot, ctx, member)
        return await ctx.send(embed=embed)

    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command()
    async def alt(self, ctx, *, member: Union[discord.Member, str] = None):
        """View player's BS statistics - alt account"""
        await ctx.trigger_typing()
        member = ctx.author if member is None else member
        embed = await player_stats.get_profile_embed(self.bot, ctx, member, alt=True)
        return await ctx.send(embed=embed)
    

    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(aliases=['b'])
    async def brawlers(self, ctx, *, member: Union[discord.Member, str] = None):
        """Brawl Stars brawlers"""
        await ctx.trigger_typing()
        member = ctx.author if member is None else member
        embeds = await player_stats.get_brawlers_embeds(self.bot, ctx, member)
        if len(embeds) > 1:
            await menu(ctx, embeds, {"⬅": prev_page, "➡": next_page}, timeout=500)
        else:
            await ctx.send(embed=embeds[0])

    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(aliases=['br'])
    async def brawler(self, ctx, brawler: str, member: Union[discord.Member, str] = None):
        """Brawler specific info"""
        await ctx.trigger_typing()
        prefix = ctx.prefix
        member = ctx.author if member is None else member
        try:
            member.id
        except AttributeError:
            return await ctx.send(embed=badEmbed(f"No such brawler found! If the brawler's name contains spaces surround it with quotes!"))
        embed = await player_stats.get_single_brawler_embed(self.bot, ctx, member, brawler)
        await ctx.send(embed=embed)
                       
    @commands.command(aliases=['e'])
    async def events(self, ctx):
        embeds = await game_stats.get_event_embeds(self.bot)
        await ctx.send(embed=embeds[0])
        if len(embeds) > 1:
            await ctx.send(embed=embeds[1])
                        
    @commands.command(aliases=['m'])
    async def map(self, ctx, *, map_name: str):
        embed = await game_stats.get_map_embed(self.bot, map_name)
        await ctx.send(embed=embed)
       
    def get_badge(self, badge_id):
        guild = self.bot.get_guild(717766786019360769)
        guild2 = self.bot.get_guild(881132228858486824)
        em = discord.utils.get(guild.emojis, name=str(badge_id))
        if em is None:
            em = discord.utils.get(guild2.emojis, name=str(badge_id))
        return str(em)

    @commands.command()
    async def bslb(self, ctx, *, region):
        try:
            lb = await self.ofcbsapi.get_rankings(ranking="clubs", region=region)
        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        embeds = []
        result = ""
        country = pycountry.countries.get(alpha_2=region)
        name = region[:30].upper() if country is None else country.name.upper()
        for club in lb:
            cname = club['name'].replace('*', '').replace('_', '-').replace('\\', '/')
            line = f"`{club['rank']:03d}` **{cname}** {club['tag']} `{club['trophies']}` {club['member_count']}\n"
            if len(result) + len(line) > 2000:
                embeds.append(discord.Embed(colour=discord.Color.random(), description=result, title=name))
                result = ""
            else:
                result += line
        if result != "":
            embeds.append(discord.Embed(colour=discord.Color.random(), description=result))
        await menu(ctx, embeds, {"⬆️": prev_page, "⬇️": next_page, }, timeout=300)
                                            
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command()
    async def club(self, ctx, key: Union[discord.Member, str] = None, keyword = None):
        """View player's club or club saved in a server"""
        await ctx.trigger_typing()
        if key is None:
            mtag = await self.config.user(ctx.author).tag()
            if mtag is None:
                return await ctx.send(embed=badEmbed(f"You have no tag saved! Use {ctx.prefix}bssave <tag>"))
            try:
                player = await self.ofcbsapi.get_player(mtag)
                if not "tag" in player.raw_data["club"]:
                    return await ctx.send("This user is not in a club!")
                tag = player.club.tag
            except brawlstats.errors.RequestError as e:
                return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        elif isinstance(key, discord.Member):
            member = key
            mtag = await self.config.user(member).tag()
            if mtag is None:
                return await ctx.send(embed=badEmbed(f"This user has no tag saved! Use {ctx.prefix}bssave <tag>"))
            try:
                player = await self.ofcbsapi.get_player(mtag)
                if not "tag" in player.raw_data["club"]:
                    return await ctx.send("This user is not in a club!")
                tag = player.club.tag
            except brawlstats.errors.RequestError as e:
                return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))
        elif key.startswith("#"):
            tag = key.upper().replace('O', '0')
        else:
            tag = await self.config.guild(ctx.guild).clubs.get_raw(key.lower(), "tag", default=None)
            if tag is None:
                return await ctx.send(embed=badEmbed(f"{key.title()} isn't saved club in this server!"))
        try:
            club = await self.ofcbsapi.get_club(tag)

        except brawlstats.errors.NotFoundError:
            return await ctx.send(embed=badEmbed("No club with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        if keyword is None:
            if club.description is not None:
                embed = discord.Embed(description=f"```{discord.utils.escape_markdown(club.description)}```")
            else:
                embed = discord.Embed(description="```None```")
            embed.set_author(name=f"{club.name} {club.tag}", icon_url=f"https://cdn.brawlify.com/club/{club.raw_data['badgeId']}.png")
            embed.add_field(
                name="Total Trophies",
                value=f"<:bstrophy:552558722770141204> `{club.trophies}`")
            embed.add_field(
                name="Required Trophies",
                value=f"{get_league_emoji(club.required_trophies)} `{club.required_trophies}`")
            if len(club.members) != 0:
                embed.add_field(
                    name="Average Trophies",
                    value=f"<:bstrophy:552558722770141204> `{club.trophies//len(club.members)}`")
            for m in club.members:
                if m.role == "president":
                    embed.add_field(
                        name="President",
                        value=f"{get_league_emoji(m.trophies)}`{m.trophies}` {discord.utils.escape_markdown(m.name)}")
                    break
            embed.add_field(
                name="Members",
                value=f"<:icon_gameroom:553299647729238016> {len(club.members)}/30")
            embed.add_field(
                name="Status",
                value=f"{club_status[club.type.lower()]['emoji']} {club_status[club.type.lower()]['name']}"
            )
            topm = ""
            for m in club.members[:5]:
                topm += f"{get_league_emoji(m.trophies)}`{m.trophies}` {discord.utils.escape_markdown(m.name)}\n"
            worstm = ""
            for m in club.members[-5:]:
                worstm += f"{get_league_emoji(m.trophies)}`{m.trophies}` {discord.utils.escape_markdown(m.name)}\n"
            if topm != "":
                embed.add_field(name="Top Members", value=topm, inline=True)
            if worstm != "":
                embed.add_field(name="Lowest Members", value=worstm, inline=True)
            else:
                return await ctx.send(embed=randomize_colour(embed))
        elif keyword in ["memberlist", "members", "list", "m", "ml"]:
            colour = choice([discord.Colour.green(),
                             discord.Colour.blue(),
                             discord.Colour.purple(),
                             discord.Colour.orange(),
                             discord.Colour.red(),
                             discord.Colour.teal()])
            startingembed = discord.Embed(colour=colour, title=f"{club.name} {club.tag}")
            mems = {}
            embedfields = []
            rank = 1
            for mem in club.members:
                if mem.role.lower() == 'vicepresident':
                    mems.update({f"{get_league_emoji(mem.trophies)}`{mem.trophies}`**{remove_codes(mem.name)}** {mem.tag}": "vp"})
                elif mem.role.lower() == 'president':
                    mems.update({f"{get_league_emoji(mem.trophies)}`{mem.trophies}`**{remove_codes(mem.name)}** {mem.tag}" : "pres"})
                elif mem.role.lower() == 'senior':
                    mems.update({f"{get_league_emoji(mem.trophies)}`{mem.trophies}`**{remove_codes(mem.name)}** {mem.tag}" : "senior"})
                elif mem.role.lower() == 'member':
                    mems.update({f"{get_league_emoji(mem.trophies)}`{mem.trophies}`**{remove_codes(mem.name)}** {mem.tag}" : "member"})
                e_name = f"__**{rank}**__ {remove_codes(mem.name)}: {mem.tag}"
                e_value= f" {get_league_emoji(mem.trophies)}`{mem.trophies}` <:people:449645181826760734>  ️{mem.role.capitalize()}"
                rank = rank + 1
                embedfields.append([e_name, e_value])

            senior_count = 0
            vp_count = 0
            pres_value = ""
            vp_value = ""
            senior_value = ""
            for item in mems.items():
                if item[1] == "pres":
                    pres_value = item[0]
                elif item[1] == "vp":
                    vp_count = vp_count + 1
                    vp_value = vp_value + f"{item[0]}\n"
                elif item[1] == "senior":
                    senior_count = senior_count + 1
                    senior_value = senior_value + f"{item[0]}\n"

            startingembed.add_field(name="President", value=pres_value)
            if vp_value == "":
                startingembed.add_field(name=f"Vice Presidents: {vp_count}", value="None", inline=False)
            elif len(vp_value) >= 1024:
                startingembed.add_field(name=f"Vice Presidents: {vp_count}", value="Too many to show", inline=False)
            else:
                startingembed.add_field(name=f"Vice Presidents: {vp_count}", value=vp_value, inline=False)
            if senior_value == "":
                startingembed.add_field(name=f"Seniors: {senior_count}", value="None", inline=False)
            elif len(senior_value) >= 1024:
                startingembed.add_field(name=f"Seniors: {senior_count}", value="Too many to show", inline=False)
            else:
                startingembed.add_field(name=f"Seniors: {senior_count}", value=senior_value, inline=False)

            embedstosend = []
            embedstosend.append(startingembed)
            for i in range(0, len(embedfields), 19):
                embed = discord.Embed(color=colour, title=f"{club.name} {club.tag}")
                for e in embedfields[i:i + 19]:
                    embed.add_field(name=e[0], value=e[1], inline=False)
                embedstosend.append(embed)

            for i in range(len(embedstosend)):
                embedstosend[i].set_footer(text=f"Page {i + 1}/{len(embedstosend)}\nScroll down for the full member list")

            if len(embedstosend) > 1:
                await menu(ctx, embedstosend, {"⬆️": prev_page, "⬇️": next_page, }, timeout=2000)
            else:
                await ctx.send(embed=embedstosend[0])
        elif keyword == "log":
            url = "https://api.brawlapi.com/clublog/" + club.tag.replace("#", "")
            log = await self.starlist_request(url)
            if log['status'] == "trackingDisabled":
                return await ctx.send(embed=badEmbed(f"Tracking for this club isn't enabled on brawlify.com website!"))
            if log['status'] != "ok":
                return await ctx.send(embed=badEmbed(f"Something went wrong. Please try again later! (Status: {log['status']})"))
            msg = ""
            for h in log['history']:
                time = h['timeFormat']
                if h['type'] == "members":
                    name = discord.utils.escape_markdown(h['data']['player']['name'])
                    tag = "#" + h['data']['player']['tag']
                    addition = f"🟢[{time}] **{name}** {tag} **joined**\n" if h["data"]["joined"] else f"🔴[{time}] **{name}** {tag} **left**\n"
                elif h['type'] == 'settings':
                    if h['data']['type'] == "description":
                        dold = h['data']['old'].replace('`','')
                        dold = "empty" if dold == "" else dold
                        dnew = h['data']['new'].replace('`','')
                        dnew = "empty" if dnew == "" else dnew    
                        addition = f"🛠️[{time}] **Description** changed to ```{dnew}```"
                    elif h['data']['type'] == "requirement":
                        old = h['data']['old']
                        new = h['data']['new']
                        addition = f"🛠️[{time}] **Requirement** changed from `{old}` to `{new}`\n"
                    elif h['data']['type'] == "status":
                        sold = h['data']['old']
                        snew = h['data']['new']
                        addition = f"🛠️[{time}] **Status** changed from `{sold}` to `{snew}`\n"
                    else:
                        stype = h['data']['type']
                        addition = f"Unrecognized setting type: `{stype}`\n"
                elif h['type'] == "roles":
                    if h['data']['promote']:
                        action = "promoted"
                        emoji = "🔺"
                    else:
                        action = "demoted"
                        emoji = "🔻"
                    rname = discord.utils.escape_markdown(h['data']['player']['name'])
                    rtag = "#" + h['data']['player']['tag']
                    rold = h['data']['old']
                    rnew = h['data']['new']
                    addition = f"{emoji}[{time}] **{rname}** {rtag} **{action}** from `{rold}` to `{rnew}`!\n"
                else:
                    type = h['type']
                    addition = f"Unrecognized type: {type}\n"
                if len(msg) + len(addition) > 2024:
                    break
                msg += addition

            colour = choice([discord.Colour.green(),
                             discord.Colour.blue(),
                             discord.Colour.purple(),
                             discord.Colour.orange(),
                             discord.Colour.red(),
                             discord.Colour.teal()])

            embed = discord.Embed(colour=colour, title=f"{club.name} {club.tag}", description=msg)
            embed.set_footer(text="Data provided by brawlify.com")

            await ctx.send(embed=embed)                    
        else:
            return await ctx.send(embed=badEmbed(f"There's no such keyword: {keyword}."))

    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def clubs(self, ctx, *, keyword: str = ""):
        """View all clubs saved in a server"""
        offline = False
        low_clubs = False
        roles = False
        skip_errors = False
        reverse_order = False
        regions = False
        membersforhawk = False
        trophy_range = False
        await ctx.trigger_typing()
        if "offline" in keyword:
            offline = True
            keyword = keyword.replace("offline", "").strip()

        if "low" in keyword:
            low_clubs = True
            keyword = keyword.replace("low", "").strip()
            low_amount = None
            for k in keyword.split(" "):
                if k.strip().isdigit():
                    low_amount = int(k)
                    keyword = keyword.replace(str(low_amount), "")
                    break

        if "roles" in keyword:
            roles = True
            keyword = keyword.replace("roles", "").strip()
                                      
        if "regions" in keyword:
            regions = True
            keyword = keyword.replace("regions", "").strip()

        if "skiperrors" in keyword:
            skip_errors = True
            keyword = keyword.replace("skiperrors", "").strip()

        if "reverse" in keyword:
            reverse_order = True
            keyword = keyword.replace("reverse", "").strip()

        if "members" in keyword:
            membersforhawk = True
            membersnumber = None
            for k in keyword.split(" "):
                if k.strip().isdigit():
                    membersnumber = int(k)
                    break
            if membersnumber is None:
                await ctx.send(embed=badEmbed(f"Looks like you didn't enter a valid member count!"))
                keyword = keyword.replace("members", "").strip()
            elif membersnumber is not None:
                keyword = keyword.replace("members", "").replace(str(membersnumber), "").strip()


        if "icanjoin" in keyword:
            trophy_range = True
            trange = None
            for k in keyword.split(" "):
                if k.strip().isdigit():
                    trange = int(k)
                    break
            if trange is None:
                tag = await self.config.user(ctx.author).tag()
                player = await self.ofcbsapi.get_player(tag)
                trange = player.trophies
                keyword = keyword.replace("icanjoin", "").strip()
            elif trange is not None:
                keyword = keyword.replace("icanjoin", "").replace(str(trange), "").strip()
                                  
        saved_clubs = await self.config.guild(ctx.guild).clubs()
        clubs_count = len(saved_clubs.keys())
        load_animation = clubs_count > 10 and not offline

        if clubs_count < 1:
            return await ctx.send(
                embed=badEmbed(f"This server has no clubs saved. Save a club by using {ctx.prefix}clubs add!"))
                                  
        loading_bar = [
            "<:blankleft:821065351907246201>" + 6 * "<:blankmid:821065351294615552>" + "<:blankright:821065351621115914>" + "⠀",
            "<:loadleft:821065351726366761>" + "<:loadmid:821065352061780048>" + 5 * "<:blankmid:821065351294615552>" + "<:blankright:821065351621115914>" + "⠀",
            "<:loadleft:821065351726366761>" + 3 * "<:loadmid:821065352061780048>" + 3 * "<:blankmid:821065351294615552>" + "<:blankright:821065351621115914>" + "⠀",
            "<:loadleft:821065351726366761>" + 5 * "<:loadmid:821065352061780048>" + "<:blankmid:821065351294615552>" + "<:blankright:821065351621115914>" + "⠀",
            "<:loadleft:821065351726366761>" + 6 * "<:loadmid:821065352061780048>" + "<:loadright:821065351903182889>" + "⠀"
        ]

        if load_animation:
            loadingembed = discord.Embed(colour=discord.Colour.red(), title="Requesting club data", description=loading_bar[0])
            msg = await ctx.send(embed=loadingembed)

        try:
            clubs = []
            keys = saved_clubs.keys()
            for ind, key in enumerate(keys):
                if offline:
                    break
                if keyword == "":
                    try:
                        club = await self.ofcbsapi.get_club(saved_clubs[key]['tag'])
                    except brawlstats.errors.RequestError as e:
                        if skip_errors:
                            continue
                        else:
                            offline = True
                            break
                    clubs.append(club)
                elif keyword != "":
                    if "family" in saved_clubs[key] and saved_clubs[key]['family'] == keyword:
                        try:
                            club = await self.ofcbsapi.get_club(saved_clubs[key]['tag'])
                        except brawlstats.errors.RequestError as e:
                             return await ctx.send(embed=badEmbed(f"Can't return family clubs, API is offline"))
                        clubs.append(club)
                if not offline and load_animation:
                    if 0.15 <= ind / len(keys) <= 0.25:
                        if loadingembed.description != loading_bar[1]:
                            loadingembed = discord.Embed(colour=discord.Colour.red(), title="Requesting club data",
                                                            description=loading_bar[1])
                            await msg.edit(embed=loadingembed)
                    elif 0.4 <= ind / len(keys) <= 0.5:
                        if loadingembed.description != loading_bar[2]:
                            loadingembed = discord.Embed(colour=discord.Colour.red(), title="Requesting club data",
                                                            description=loading_bar[2])
                            await msg.edit(embed=loadingembed)
                    elif 0.65 <= ind / len(keys) <= 0.75:
                        if loadingembed.description != loading_bar[3]:
                            loadingembed = discord.Embed(colour=discord.Colour.red(), title="Requesting club data",
                                                            description=loading_bar[3])
                            await msg.edit(embed=loadingembed)
                    elif 0.9 <= ind / len(keys) <= 1:
                        if loadingembed.description != loading_bar[4]:
                            loadingembed = discord.Embed(colour=discord.Colour.red(), title="Requesting club data",
                                                            description=loading_bar[4])
                            await msg.edit(embed=loadingembed)
                #await asyncio.sleep(0.3)

            embedFields = []

            #if load_animation:
                #loadingembed = discord.Embed(colour=discord.Colour.red(), description="Almost there!", title="Creating the embed...")
                #await msg.edit(embed=loadingembed)
            if not offline:
                clubs = sorted(clubs, key=lambda sort: (sort.trophies), reverse=not reverse_order)

                for i in range(len(clubs)):
                    key = ""
                    for k in saved_clubs.keys():
                        if clubs[i].tag.replace("#", "") == saved_clubs[k]['tag']:
                            key = k
                                            
                    badge_id = clubs[i].raw_data['badgeId']
                    badge_emoji = self.get_badge(badge_id)
                                            
                    if badge_emoji is None:
                        badge_emoji = "<:bsband:600741378497970177>"
                    
                    saved_clubs[key]['lastMemberCount'] = len(clubs[i].members)
                    saved_clubs[key]['lastRequirement'] = clubs[i].required_trophies
                    saved_clubs[key]['lastScore'] = clubs[i].trophies
                    saved_clubs[key]['lastPosition'] = i
                    saved_clubs[key]['lastStatus'] = clubs[i].type
                    saved_clubs[key]['lastBadge'] = badge_id
                    
                    info = saved_clubs[key]["info"] if "info" in saved_clubs[key] else ""
                    role = ctx.guild.get_role(saved_clubs[key]["role"]) if "role" in saved_clubs[key] else None
                    region = (saved_clubs[key]["family"] + '\n') if ("family" in saved_clubs[key] and regions) else ""

                    if low_clubs:
                        if low_amount is None and len(clubs[i].members) >= 25:
                            continue
                        if low_amount is not None and len(clubs[i].members) > low_amount:
                            continue

                    if membersforhawk:
                        if len(clubs[i].members) != membersnumber:
                            continue

                    if trophy_range:
                        if clubs[i].required_trophies > trange:
                            continue

                    e_name = f"{badge_emoji} {clubs[i].name} [{key}] {clubs[i].tag} {info}"
                    role_info = f"{role.mention}\n" if roles and role is not None else ""
                    e_value = f"{role_info}{region}{club_status[clubs[i].type.lower()]['emoji']} <:bstrophy:552558722770141204>`{clubs[i].trophies}` {get_league_emoji(clubs[i].required_trophies)}"
                    e_value += f"`{clubs[i].required_trophies}+` <:icon_gameroom:553299647729238016>`{len(clubs[i].members)}`"
                    embedFields.append([e_name, e_value])

                await self.config.guild(ctx.guild).set_raw("clubs", value=saved_clubs)

            else:
                offclubs = []
                for k in saved_clubs.keys():
                    offclubs.append([saved_clubs[k]['lastPosition'], k])
                offclubs = sorted(offclubs, key=lambda x: x[0], reverse=reverse_order)

                for club in offclubs:
                    ckey = club[1]
                    cscore = saved_clubs[ckey]['lastScore']
                    cname = saved_clubs[ckey]['name']
                    ctag = saved_clubs[ckey]['tag']
                    cinfo = saved_clubs[ckey]['info']
                    cmembers = saved_clubs[ckey]['lastMemberCount']
                    creq = saved_clubs[ckey]['lastRequirement']
                    ctype = saved_clubs[ckey]['lastStatus']
                    cbadge = saved_clubs[ckey]['lastBadge']
                                            
                    badge_emoji = self.get_badge(cbadge)

                    if badge_emoji is None:
                        badge_emoji = "<:bsband:600741378497970177>"
                                           
                    if low_clubs:
                        if low_amount is None and cmembers >= 95:
                            continue
                        if low_amount is not None and cmembers > low_amount:
                            continue

                    if membersforhawk:
                        if len(clubs[i].members) != membersnumber:
                            continue

                    if trophy_range:
                        if creq > trange:
                            continue

                    e_name = f"{badge_emoji} {cname} [{ckey}] #{ctag} {cinfo}"
                    e_value = f"{club_status[ctype.lower()]['emoji']} <:bstrophy:552558722770141204>`{cscore}` {get_league_emoji(creq)}`{creq}+` <:icon_gameroom:553299647729238016>`{cmembers}`)"
                    embedFields.append([e_name, e_value])

            colour = choice([discord.Colour.green(),
                             discord.Colour.blue(),
                             discord.Colour.purple(),
                             discord.Colour.orange(),
                             discord.Colour.red(),
                             discord.Colour.teal()])
            embedsToSend = []
            for i in range(0, len(embedFields), 8):
                embed = discord.Embed(colour=colour)
                embed.set_author(
                    name=f"{ctx.guild.name} clubs",
                    icon_url=ctx.guild.icon_url)
                page = (i // 8) + 1
                footer = f"[{page}/{math.ceil(len(embedFields)/8)}] API is offline, showing last saved data." if offline else f"[{page}/{len(embedFields)//8+1}] Need more info about a club? Use {ctx.prefix}club [key]"
                embed.set_footer(text=footer)
                for e in embedFields[i:i + 8]:
                    embed.add_field(name=e[0], value=e[1], inline=False)
                embedsToSend.append(embed)

            if load_animation:
                await msg.delete()
            if len(embedsToSend) > 1:
                await menu(ctx, embedsToSend, {"⬅": prev_page, "➡": next_page}, timeout=2000)
            elif len(embedsToSend) == 1:
                await ctx.send(embed=embedsToSend[0])
            else:
                await ctx.send("No clubs found!")

        except ZeroDivisionError as e:
            return await ctx.send(
                "**Something went wrong, please send a personal message to Modmail bot or try again!**")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @clubs.command(name="add")
    async def clubs_add(self, ctx, key: str, tag: str):
        """
        Add a club to /clubs command
        key - key for the club to be used in other commands
        tag - in-game tag of the club
        """
        await ctx.trigger_typing()
        if tag.startswith("#"):
            tag = tag.strip('#').upper().replace('O', '0')

        if key in (await self.config.guild(ctx.guild).clubs()).keys():
            return await ctx.send(embed=badEmbed("This club is already saved!"))

        try:
            club = await self.ofcbsapi.get_club(tag)
            result = {
                "name": club.name,
                "nick": key.title(),
                "tag": club.tag.replace("#", ""),
                "lastMemberCount": club.members_count,
                "lastRequirement": club.required_trophies,
                "lastScore": club.trophies,
                "lastStatus" : club.type,
                "info": "",
                "role": None,
                "lastBadge" : ""
            }
            key = key.lower()
            await self.config.guild(ctx.guild).clubs.set_raw(key, value=result)
            await ctx.send(embed=goodEmbed(f"{club.name} was successfully saved in this server!"))

        except brawlstats.errors.NotFoundError as e:
            await ctx.send(embed=badEmbed("No club with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send("**Something went wrong, please send a personal message to Modmail bot or try again!**")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @clubs.command(name="remove")
    async def clubs_remove(self, ctx, key: str):
        """
        Remove a club from /clubs command
        key - key for the club used in commands
        """
        await ctx.trigger_typing()
        key = key.lower()

        try:
            name = await self.config.guild(ctx.guild).clubs.get_raw(key, "name")
            await self.config.guild(ctx.guild).clubs.clear_raw(key)
            await ctx.send(embed=goodEmbed(f"{name} was successfully removed from this server!"))
        except KeyError:
            await ctx.send(embed=badEmbed(f"{key.title()} isn't saved club!"))

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @clubs.command(name="info")
    async def clubs_info(self, ctx, key: str, *, info: str = ""):
        """Edit club info"""
        await ctx.trigger_typing()
        key = key.lower()

        try:
            await self.config.guild(ctx.guild).clubs.set_raw(key, "info", value=info)
            await ctx.send(embed=goodEmbed("Club info successfully edited!"))
        except KeyError:
            await ctx.send(embed=badEmbed(f"{key.title()} isn't saved club in this server!"))

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @clubs.command(name="role")
    async def clubs_role(self, ctx, key: str, role: discord.Role = None):
        """Add a role to club"""
        await ctx.trigger_typing()
        key = key.lower()

        try:
            if await self.config.guild(ctx.guild).clubs.get_raw(key, "tag") is None:
                return await ctx.send(embed=badEmbed(f"{key.title()} isn't saved club in this server!"))
            await self.config.guild(ctx.guild).clubs.set_raw(key, "role", value=role.id if role is not None else None)
            name = role.name if role is not None else "None"
            await ctx.send(embed=goodEmbed(f"Club role set to {name}!"))
        except KeyError:
            await ctx.send(embed=badEmbed(f"{key.title()} isn't saved club in this server!"))

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @clubs.command(name="region")
    async def clubs_region(self, ctx, key: str, *, family: str = ""):
        """Edit club's region"""
        await ctx.trigger_typing()
        key = key.lower()
        try:
            await self.config.guild(ctx.guild).clubs.set_raw(key, "family", value=family)
            await ctx.send(embed=goodEmbed("Club region successfully edited!"))
        except KeyError:
            await ctx.send(embed=badEmbed(f"{key.title()} isn't saved club in this server!"))

    async def removeroleifpresent(self, member: discord.Member, *roles):
        msg = ""
        for role in roles:
            if role is None:
                continue
            if role in member.roles:
                await member.remove_roles(role)
                msg += f"Removed **{str(role)}**\n"
        return msg

    async def addroleifnotpresent(self, member: discord.Member, *roles):
        msg = ""
        for role in roles:
            if role is None:
                continue
            if role not in member.roles:
                await member.add_roles(role)
                msg += f"Added **{str(role)}**\n"
        return msg

    @commands.command()
    @commands.guild_only()
    async def userbytag(self, ctx, tag: str):
        """Find user with a specific tag saved"""
        tag = tag.lower().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        for user in (await self.config.all_users()):
            person = self.bot.get_user(user)
            if person is not None:
                if (await self.config.user(person).tag()) == tag:
                    return await ctx.send(f"This tag belongs to **{str(person)}**.")
        await ctx.send("This tag is either not saved or invalid.")

    @commands.command()
    @commands.guild_only()
    async def usersbyclub(self, ctx, tag: str):
        """Find users, who have tag saved, in a specified club"""
        tag = tag.upper().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        msg = ""
        count = 0
        club = await self.ofcbsapi.get_club(tag)
        for user in (await self.config.all_users()):
            person = self.bot.get_user(user)
            if person is not None:
                persontag = await self.config.user(person).tag()
                persontag = "#" + persontag.upper()
                for member in club.members:
                    if member.tag == persontag:
                        msg += f"Tag: **{str(person)}**; IGN: **{member.name}**\n"
                        count = count + 1

        if msg == "":
            await ctx.send(embed=discord.Embed(description="This tag is either invalid or no people from this club saved their tags.", colour=discord.Colour.red()))
        else:
            await ctx.send(embed=discord.Embed(title=f"Total: {count}", description=msg, colour=discord.Colour.blue()))

    @commands.command(aliases=['vpsbyclub'])
    @commands.guild_only()
    async def vpbyclub(self, ctx, tag: str):
        """Find vicepresidents, who have tag saved, in a specified club"""
        tag = tag.upper().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        msg = ""
        count = 0
        club = await self.ofcbsapi.get_club(tag)
        for user in (await self.config.all_users()):
            person = self.bot.get_user(user)
            if person is not None:
                persontag = await self.config.user(person).tag()
                persontag = "#" + persontag.upper()
                for member in club.members:
                    if member.tag == persontag and member.role.lower() == "vicepresident":
                        msg += f"Tag: **{str(person)}**; IGN: **{member.name}**\n"
                        count = count + 1

        if msg == "":
            await ctx.send(embed=discord.Embed(
                description="This tag is either invalid or no people from this club saved their tags.", colour=discord.Colour.red()))
        else:
            await ctx.send(embed=discord.Embed(title=f"Total: {count}", description=msg, colour=discord.Colour.blue()))

    @commands.command()
    @commands.guild_only()
    async def presbyclub(self, ctx, tag: str):
        """Find a club president, who have tag saved, in a specified club"""
        tag = tag.upper().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        msg = ""
        count = 0
        club = await self.ofcbsapi.get_club(tag)
        for user in (await self.config.all_users()):
            person = self.bot.get_user(user)
            if person is not None:
                persontag = await self.config.user(person).tag()
                persontag = "#" + persontag.upper()
                for member in club.members:
                    if member.tag == persontag and member.role.lower() == "president":
                        msg += f"Tag: **{str(person)}**; IGN: **{member.name}**\n"
                        count = count + 1

        if msg == "":
            await ctx.send(embed=discord.Embed(
                description="This tag is either invalid or no people from this club saved their tags.", colour=discord.Colour.red()))
        else:
            await ctx.send(embed=discord.Embed(title=f"Total: {count}", description=msg, colour=discord.Colour.blue()))

    @commands.command()
    @commands.guild_only()
    async def membersBS(self, ctx, *, rolename):
        role = None
        for r in ctx.guild.roles:
            if r.name.lower() == rolename.lower():
                role = r
                continue
            elif r.name.lower().startswith(rolename.lower()):
                role = r
                continue
        if role is None:
            await ctx.send("No such role in the server.")
            return
        result = role.members
        if not result:
            await ctx.send("No members with such role in the server.")
            return
        discordn = ""
        ign = ""
        clubn = ""
        discords = []
        igns = []
        clubs = []
        for member in result:
            tag = await self.config.user(member).tag()
            if tag is not None:
                player = await self.ofcbsapi.get_player(tag)
                player_in_club = "name" in player.raw_data["club"]
            if len(discordn) > 666 or len(ign) > 666 or len(clubn) > 666:
                discords.append(discordn)
                discordn = ""
                igns.append(ign)
                ign = ""
                clubs.append(clubn)
                clubn = ""
            if tag is None:
                discordn += f"{str(member)}\n"
                ign += "None\n"
                clubn += "None\n"
            elif player_in_club:
                club = await self.ofcbsapi.get_club(player.club.tag)
                for mem in club.members:
                    if mem.tag == player.tag:
                        discordn += f"{str(member)}\n"
                        ign += f"{player.name}\n"
                        clubn += f"{player.club.name}({mem.role.capitalize()})\n"
            elif not player_in_club:
                discordn += f"{str(member)}\n"
                ign += f"{player.name}\n"
                clubn += "None\n"
            await asyncio.sleep(0.1)
        if len(discordn) > 0 or len(ign) > 0 or len(clubn) > 0:
            discords.append(discordn)
            igns.append(ign)
            clubs.append(clubn)
        i = 0
        while i < len(discords):
            embed = discord.Embed(color=discord.Colour.green(), title=f"Members: {str(len(result))}\n")
            embed.add_field(name="Discord", value=discords[i], inline=True)
            embed.add_field(name="IGN", value=igns[i], inline=True)
            embed.add_field(name="Club(Role)", value=clubs[i], inline=True)
            await ctx.send(embed=embed)
            i = i + 1
