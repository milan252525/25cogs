import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.embed import randomize_colour
from redbot.core.utils.menus import menu, prev_page, next_page
from discord.ext import tasks

from .utils import *

from random import choice
import asyncio
import brawlstats
from typing import Union
from re import sub
import datetime
import aiohttp
from cachetools import TTLCache
from fuzzywuzzy import process
from operator import itemgetter, attrgetter
from quickchart import QuickChart

class BrawlStarsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=5245652)
        default_user = {"tag": None, "alt": None, "name" : "", "altname" : ""}
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
        header = {"Authorization": f"Bearer {self.starlist_key}"}
        async with self.aiohttp_session.get(url, headers=header) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                return {'status': str(resp.status) + " " + resp.reason}
            
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guilds = (401883208511389716, 616673259538350084, 674348799673499671, 663716223258984496)
        channels = (547087959015292929, 616696393729441849, 674348799673499671, 663803544276828171)
        if member.guild.id in guilds:
            tag = await self.config.user(member).tag()
            if tag is not None:
                ch = member.guild.get_channel(channels[guilds.index(member.guild.id)])
                embed = discord.Embed(colour=discord.Colour.blue(), description=f"#{tag.upper()}")
                embed.set_author(name=member.display_name, icon_url=member.avatar_url)
                await asyncio.sleep(3)
                await ch.send(embed=embed)


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
            await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!****")

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
            await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!****")

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
        prefix = ctx.prefix
        tag = ""

        member = ctx.author if member is None else member

        if isinstance(member, discord.Member):
            tag = await self.config.user(member).tag()
            if tag is None:
                return await ctx.send(embed=badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))
        elif member.startswith("#"):
            tag = member.upper().replace('O', '0')
        else:
            try:
                member = self.bot.get_user(int(member))
                if member is not None:
                    tag = await self.config.user(member).tag()
                    if tag is None:
                        return await ctx.send(embed=badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))
            except ValueError:
                member = discord.utils.get(ctx.guild.members, name=member)
                if member is not None:
                    tag = await self.config.user(member).tag()
                    if tag is None:
                        return await ctx.send(embed=badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))

        if tag is None or tag == "":
            desc = "/p\n/bsprofile @user\n/p discord_name\n/p discord_id\n/p #BSTAG"
            embed = discord.Embed(
                title="Invalid argument!",
                colour=discord.Colour.red(),
                description=desc)
            return await ctx.send(embed=embed)
        
        main = True
        has_alt = (await self.config.user(member).alt() is not None) if type(member) == discord.Member else False

        if type(member) == discord.Member and has_alt:
            tagg = await self.config.user(member).tag()
            altt = await self.config.user(member).alt()
            name_main = await self.config.user(member).name()
            main_text = f" `{name_main}` " if name_main != "" else ""
            alt_name = await self.config.user(member).altname()
            alt_text = f" `{alt_name}` " if alt_name != "" else ""
            tagg = main_text + "#" + tagg.upper()
            altt = alt_text + "#" + altt.upper()
            prompt = await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(),
                                                        title="Which one of the accounts would you like to see?", description=f"1️⃣ {tagg}\n2️⃣ {altt}"))
            await prompt.add_reaction("1️⃣")
            await prompt.add_reaction("2️⃣")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["1️⃣", "2️⃣"]

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            except asyncio.TimeoutError:
                return await prompt.delete()

            if str(reaction.emoji) == "1️⃣":
                tag = await self.config.user(member).tag()
            elif str(reaction.emoji) == "2️⃣":
                tag = await self.config.user(member).alt()
                main = False

            await prompt.delete()

        try:
            player = await self.ofcbsapi.get_player(tag)

        except brawlstats.errors.NotFoundError:
            return await ctx.send(embed=badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send("****Something went wrong, please send a personal message to LA Modmail bot or try again!****")

        if main and type(member) == discord.Member and has_alt:
            await self.config.user(member).name.set(player.name)
            
        if not main and type(member) == discord.Member:
            await self.config.user(member).altname.set(player.name)
            
        colour = player.name_color if player.name_color is not None else "0xffffffff"
        embed = discord.Embed(color=discord.Colour.from_rgb(
            int(colour[4:6], 16), int(colour[6:8], 16), int(colour[8:10], 16)))
        player_icon_id = player.raw_data["icon"]["id"]
        if self.icons is None:
            self.icons = await self.starlist_request("https://api.starlist.pro/icons")
        if self.icons['status'] == 'ok' and self.icons is not None:
            player_icon = self.icons['player'][str(player_icon_id)]['imageUrl2']
        else:
            self.icons = None
            player_icon = member.avatar_url
        embed.set_author(
            name=f"{player.name} {player.raw_data['tag']}",
            icon_url=player_icon)
        embed.add_field(
            name="Trophies",
            value=f"{get_league_emoji(player.trophies)} {player.trophies}")
        embed.add_field(
            name="Highest Trophies",
            value=f"{get_league_emoji(player.highest_trophies)} {player.highest_trophies}")
        embed.add_field(
            name="Level",
            value=f"<:exp:614517287809974405> {player.exp_level}")
        star_powers = sum([len(x.star_powers) for x in player.brawlers])
        gadgets = sum([len(x['gadgets']) for x in player.raw_data['brawlers']])
        embed.add_field(
            name="Unlocked Brawlers",
            value=f"<:brawlers:614518101983232020> {len(player.brawlers)} <:star_power:729732781638156348> {star_powers} <:gadget:716341776608133130> {gadgets}")
        if "tag" in player.raw_data["club"]:
            try:
                club = await self.ofcbsapi.get_club(player.club.tag)
                embed.add_field(name="Club", value=f"{self.get_badge(club.raw_data['badgeId'])} {player.club.name}")
                for m in club.members:
                    if m.tag == player.raw_data['tag']:
                        embed.add_field(name="Role", value=f"<:role:614520101621989435> {m.role.capitalize()}")
                        break
            except brawlstats.errors.RequestError:
                embed.add_field(name="Club", value=f"<:bsband:600741378497970177> {player.club.name}")
                embed.add_field(
                    name="Role",
                    value=f"<:offline:642094554019004416> Error while retrieving role")
        else:
            embed.add_field(
                name="Club",
                value=f"<:noclub:661285120287834122> Not in a club")
        embed.add_field(
            name="3v3 Wins",
            value=f"{get_gamemode_emoji(get_gamemode_id('gemgrab'))} {player.raw_data['3vs3Victories']}")
        embed.add_field(
            name="Showdown Wins",
            value=f"{get_gamemode_emoji(get_gamemode_id('showdown'))} {player.solo_victories} {get_gamemode_emoji(get_gamemode_id('duoshowdown'))} {player.duo_victories}")
        rr_levels = ["-", "Normal", "Hard", "Expert", "Master", "Insane"]
        if player.best_robo_rumble_time > 5:
            rr_level = f"Insane {player.best_robo_rumble_time - 5}"
        else:
            rr_level = rr_levels[player.best_robo_rumble_time]
        embed.add_field(
            name="Best RR Level",
            value=f"{get_gamemode_emoji(get_gamemode_id('roborumble'))} {rr_level}")
        #embed.add_field(
        #    name="Best Time as Big Brawler",
        #    value=f"<:biggame:614517022323245056> {player.best_time_as_big_brawler//60}:{str(player.best_time_as_big_brawler%60).rjust(2, '0')}")
        title_extra = ""
        value_extra = ""
        if "highestPowerPlayPoints" in player.raw_data:
            title_extra = " (Highest)"
            value_extra = f" ({player.raw_data['highestPowerPlayPoints']})"
        if "powerPlayPoints" in player.raw_data:
            embed.add_field(
                name=f"PP Points{title_extra}",
                value=f"<:powertrophies:661266876235513867> {player.raw_data['powerPlayPoints']}{value_extra}")
        else:
            embed.add_field(name=f"PP Points{title_extra}",
                            value=f"<:powertrophies:661266876235513867> 0 {value_extra}")
        reset = reset_trophies(player) - player.trophies
        embed.add_field(
            name="Season Reset",
            value=f"<:bstrophy:552558722770141204> {reset} <:starpoint:661265872891150346> {calculate_starpoints(player)}")
        emo = "<:good:450013422717763609> Qualified" if player.raw_data['isQualifiedFromChampionshipChallenge'] else "<:bad:450013438756782081> Not qualified"
        embed.add_field(name="Championship", value=f"{emo}")
        texts = [
            "Check out all your brawlers using /brawlers!", 
            "Want to see your club stats? Try /club!", 
            "Have you seen all our clubs? No? Do /clubs!",
            "You can see stats of other players by typing /p @user.",
            "You can display player's stats by using his tag! /p #TAG",
            "Did you know LA Bot can display CR stats as well? /crp",
            "Check www.laclubs.net to see all our clubs!"
        ]

        if "name" in player.raw_data["club"] and player.raw_data["club"]["name"].startswith("LA "):
            history_url = "https://localhost/api/history/player?tag=" + player.raw_data['tag'].strip("#")
            data = None
            chart_data = []
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=True)) as session:
                async with session.get(history_url) as resp:
                    data = await resp.json()
            if data is not None and data['status'] == "ok":
                for time, trophies in zip(data['times'][::2], data['trophies'][::2]):
                    chart_data.append("{t:new Date(" + str(time*1000) + "),y:" + str(trophies) + "}")
                qc = QuickChart()
                qc.config = """
                {
                    type: 'line',
                    data: {
                        datasets: [{
                            data : """ + str(chart_data).replace("\'", "") + """,
                            label: "trophies",
                            fill: true,
                            cubicInterpolationMode: 'monotone',
                            borderColor: 'rgba(10, 180, 20, 1)',
                            backgroundColor: 'rgba(10, 180, 20, 0.3)'
                        }]
                    },
                    options: {
                        scales: {
                            xAxes: [{
                                type: 'time',
                                time: {
                                    unit: 'day'
                                },
                                distribution: 'linear'
                            }]
                        },
                        responsive: false,
                        legend: {
                            display: false
                        },
                        tooltips: {
                            mode: 'index',
                            intersect: false
                        },
                        title: {
                            display: true,
                            text: 'TROPHY PROGRESSION',
                            fontStyle: 'bold'
                        },
                        layout: {
                            padding: {
                                left: 5,
                                right: 10,
                                top: 0,
                                bottom: 5
                            }
                        }
                    }
                }
                """
                embed.set_image(url=qc.get_short_url())
        embed.set_footer(text=choice(texts))
        await ctx.send(embed=embed)

    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command(aliases=['b'])
    async def brawlers(self, ctx, *, member: Union[discord.Member, str] = None):
        """Brawl Stars brawlers"""
        await ctx.trigger_typing()
        prefix = ctx.prefix
        tag = ""
        member = ctx.author if member is None else member

        if isinstance(member, discord.Member):
            tag = await self.config.user(member).tag()
            if tag is None:
                return await ctx.send(embed=badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))
        elif member.startswith("#"):
            tag = member.upper().replace('O', '0')
        else:
            try:
                member = discord.utils.get(ctx.guild.members, id=int(member))
                if member is not None:
                    tag = await self.config.user(member).tag()
                    if tag is None:
                        return await ctx.send(
                            embed=badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))
            except ValueError:
                member = discord.utils.get(ctx.guild.members, name=member)
                if member is not None:
                    tag = await self.config.user(member).tag()
                    if tag is None:
                        return await ctx.send(
                            embed=badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))

        if tag is None or tag == "":
            desc = "/b\n/brawlers @user\n/b discord_name\n/b discord_id\n/b #BSTAG"
            embed = discord.Embed(
                title="Invalid argument!",
                colour=discord.Colour.red(),
                description=desc)
            return await ctx.send(embed=embed)

        has_alt = (await self.config.user(member).alt() is not None) if type(member) == discord.Member else False

        if type(member) == discord.Member and has_alt:
            tagg = await self.config.user(member).tag()
            altt = await self.config.user(member).alt()
            name_main = await self.config.user(member).name()
            main_text = f" `{name_main}` " if name_main != "" else ""
            alt_name = await self.config.user(member).altname()
            alt_text = f" `{alt_name}` " if alt_name != "" else ""
            tagg = main_text + "#" + tagg.upper()
            altt = alt_text + "#" + altt.upper()
            prompt = await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(),
                                                        title="Which one of the accounts would you like to see?", description=f"1️⃣ {tagg}\n2️⃣ {altt}"))
            await prompt.add_reaction("1️⃣")
            await prompt.add_reaction("2️⃣")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["1️⃣", "2️⃣"]

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            except asyncio.TimeoutError:
                return await prompt.delete()

            if str(reaction.emoji) == "1️⃣":
                tag = await self.config.user(member).tag()
            elif str(reaction.emoji) == "2️⃣":
                tag = await self.config.user(member).alt()

            await prompt.delete()

        try:
            player = await self.ofcbsapi.get_player(tag)

        except brawlstats.errors.NotFoundError:
            return await ctx.send(embed=badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send(
                "****Something went wrong, please send a personal message to LA Modmail bot or try again!****")

        colour = player.name_color if player.name_color is not None else "0xffffffff"

        player_icon_id = player.raw_data["icon"]["id"]
        if self.icons is None:
            self.icons = await self.starlist_request("https://api.starlist.pro/icons")
        if self.icons['status'] == 'ok' and self.icons is not None:
            player_icon = self.icons['player'][str(player_icon_id)]['imageUrl2']
        else:
            self.icons = None
            player_icon = member.avatar_url

        brawlers = player.raw_data['brawlers']
        brawlers.sort(key=itemgetter('trophies'), reverse=True)

        embedfields = []
        
        for br in brawlers:
            rank = discord.utils.get(self.bot.emojis, name=f"rank_{br['rank']}")
            ename = f"{get_brawler_emoji(br['name'])} {br['name'].lower().title()} "
            ename += f"<:pp:664267845336825906> {br['power']}"
            evalue = f"{rank} `{br['trophies']}/{br['highestTrophies']}`\n"
            evalue += f"<:star_power:729732781638156348> `{len(br['starPowers'])}` "
            evalue += f"<:gadget:716341776608133130> `{len(br['gadgets'])}`"
            evalue = evalue.strip()
            embedfields.append([ename, evalue])
        
        embedstosend = []
        for i in range(0, len(embedfields), 15):
            embed = discord.Embed(color=discord.Colour.from_rgb(int(colour[4:6], 16), int(colour[6:8], 16), int(colour[8:10], 16)), title=f"Brawlers({len(brawlers)}/44):")
            embed.set_author(name=f"{player.name} {player.raw_data['tag']}", icon_url=player_icon)
            for e in embedfields[i:i + 15]:
                embed.add_field(name=e[0], value=e[1], inline=True)
            embedstosend.append(embed)

        for i in range(len(embedstosend)):
            embedstosend[i].set_footer(text=f"Page {i+1}/{len(embedstosend)}\n/brawler <name> for more stats")

        if len(embedstosend) > 1:
            await menu(ctx, embedstosend, {"⬅": prev_page, "➡": next_page}, timeout=2000)
        else:
            await ctx.send(embed=embedstosend[0])

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

        tag = await self.config.user(member).tag()
        if tag is None:
            return await ctx.send(embed=badEmbed(f"You have no tag saved! Use {prefix}save <tag>"))

        if tag is None or tag == "":
            desc = "/p\n/profile @user\n/p discord_name\n/p discord_id\n/p #BSTAG"
            embed = discord.Embed(
                title="Invalid argument!",
                colour=discord.Colour.red(),
                description=desc)
            return await ctx.send(embed=embed)

        try:
            player = await self.ofcbsapi.get_player(tag)
            brawler_data = (await self.starlist_request("https://api.starlist.pro/brawlers"))['list']

        except brawlstats.errors.NotFoundError:
            return await ctx.send(embed=badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send(
                "****Something went wrong, please send a personal message to LA Modmail bot or try again!****")

        if brawler.upper() == "RUFFS":
            brawler = "COLONEL RUFFS"

        unlocked = False
        br = None
        for b in player.raw_data['brawlers']:
            if b['name'] == brawler.upper():
                br = b
                unlocked = True
                break

        data = None
        for b in brawler_data:
            if b['name'].upper() == brawler.upper():
                data = b
                break

        if br is None and data is None:
            return await ctx.send(embed=badEmbed(f"No such brawler found! If the brawler's name contains spaces surround it with quotes!"))

        colour = player.name_color if player.name_color is not None else "0xffffffff"
        embed = discord.Embed(color=discord.Colour.from_rgb(
            int(colour[4:6], 16), int(colour[6:8], 16), int(colour[8:10], 16)))
        if unlocked:
            embed.set_author(name=f"{player.name}'s {data['name']}", icon_url=data['imageUrl2'])
        else:
            embed.set_author(name=f"{data['name']} (Not unlocked)", icon_url=data['imageUrl2'])
        embed.description = f"<:brawlers:614518101983232020> {data['rarity']['name']}"
        if unlocked:
            rank = discord.utils.get(self.bot.emojis, name=f"rank_{br['rank']}")
            embed.description += f" {rank} {br.get('trophies')}/{br['highestTrophies']}"
            embed.description += f" <:pp:664267845336825906> {br['power']}"
        embed.description += "\n```" + data['description'] + "```"
        embed.set_footer(text=data['class']['name'])
        starpowers = ""
        gadgets = ""
        for star in data['starPowers']:
            owned = False
            if unlocked:
                for sp in br['starPowers']:
                    if star['id'] == sp['id']:
                        owned = True
            emoji = "<:star_power:729732781638156348>" if owned else "<:sp_locked:729751963549302854>"
            starpowers += f"{emoji} {star['name']}\n`{star['description']}`\n"
        embed.add_field(name="Star Powers", value=starpowers if starpowers != "" else "No data available")
        
        for gadget in data['gadgets']:
            owned = False
            if unlocked:
                for ga in br['gadgets']:
                    if gadget['id'] == ga['id']:
                        owned = True
            emoji = "<:gadget:716341776608133130>" if owned else "<:ga_locked:729752493793476759>"
            gadgets += f"{emoji} {gadget['name']}\n`{gadget['description']}`\n"
        embed.add_field(name="Gadgets", value=gadgets if gadgets != "" else "No data available")
        await ctx.send(embed=embed)
    
    def time_left(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if hours <= 24:
            return "{}h {:02}m".format(int(hours), int(minutes))
        else:
            return f"{int(hours)//24}d {(int(hours)//24)%24}h"
                       
    @commands.command(aliases=['e'])
    async def events(self, ctx):
        events = await self.starlist_request("https://api.starlist.pro/events")
        if events['status'] != "ok":
            return await ctx.send(embed=badEmbed("Something went wrong. Please try again later!"))
        time_now = datetime.datetime.now()
        embed1 = discord.Embed(title="ACTIVE EVENTS", colour=discord.Colour.green())
        embed2 = discord.Embed(title="UPCOMING EVENTS", colour=discord.Colour.green())
        active = ""
        for ev in events['active']:
            if ev['slot']['name'] == "Duo Showdown":
                continue
            modifier = ""
            powerplay = ""
            if ev['slot']['name'] == "Power Play":
                powerplay = "<:powertrophies:661266876235513867> "
            if ev['modifier'] is not None:
                modifier = f"↳ Modifier: {ev['modifier']['name']}\n"
            active += f"**{powerplay}{get_gamemode_emoji(ev['map']['gameMode']['id'])} {ev['map']['gameMode']['name']}**\n↳ Map: {ev['map']['name']}\n{modifier}"
        embed1.description = active
        upcoming = ""
        for ev in events['upcoming']:
            if ev['slot']['name'] == "Duo Showdown":
                continue
            modifier = ""
            powerplay = ""
            challenge = ""
            if ev['slot']['name'] == "Power Play":
                powerplay = "<:powertrophies:661266876235513867> "
            if "challenge" in ev['slot']['name'].lower():
                challenge = "<:totaltrophies:614517396111097866> "
            if ev['modifier'] is not None:
                modifier = f"↳ Modifier: {ev['modifier']['name']}\n"
            start = datetime.datetime.strptime(ev['startTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
            diff = self.time_left((start - time_now).total_seconds())
            upcoming += f"**{challenge}{powerplay}{get_gamemode_emoji(ev['map']['gameMode']['id'])} {ev['map']['gameMode']['name']}**\n↳ Map: {ev['map']['name']}\n↳ Starts in: {diff}\n{modifier}"
        embed2.description = upcoming
        embed2.set_footer(text="Data provided by starlist.pro")
        await ctx.send(embed=embed1)
        await ctx.send(embed=embed2)
                        
    @commands.command(aliases=['m'])
    async def map(self, ctx, *, map_name: str):
        if self.maps is None:
            final = {}
            all_maps = await self.starlist_request("https://api.starlist.pro/maps")
            for m in all_maps['list']:
                hash_ = m['hash'] + "-old" if m['disabled'] else m['hash']
                hash_ = ''.join(i for i in hash_ if not i.isdigit())
                final[hash_] = {'url': m['imageUrl'], 'name': m['name'], 
                                   'disabled': m['disabled'], 'link': m['link'],
                                   'gm_url': m['gameMode']['imageUrl'], 'id': m['id']}
            self.maps = final
                        
        map_name = map_name.replace(" ", "-")
        result = process.extract(map_name, list(self.maps.keys()), limit=1)
        result_map = self.maps[result[0][0]]
        embed = discord.Embed(colour=discord.Colour.green() )
        embed.set_author(name=result_map['name'], url=result_map['link'], icon_url=result_map['gm_url'])
        data = (await self.starlist_request(f"https://api.starlist.pro/maps/{result_map['id']}/300-599"))['map']
        brawlers = (await self.starlist_request(f"https://api.starlist.pro/brawlers"))['list']
        if 'stats' in data:
            stats = data['stats']

            if len(stats) > 0 and 'winRate' in stats[0]:
                wr = ""
                stats.sort(key=itemgetter('winRate'), reverse=True)
                for counter, br in enumerate(stats[:10], start=1):
                    name = None
                    for b in brawlers:
                        if b['id'] == br['brawler']:
                            name = b['name'].upper()
                            break
                    if name is None:
                        continue                               
                    wr += f"{get_brawler_emoji(name)} `{int(br['winRate'])}%` "
                    if counter % 5 == 0:
                        wr += "\n"
                embed.add_field(name="Best Win Rates", value=wr, inline=False)

            if len(stats) > 0 and 'bossWinRate' in stats[0]:
                bwr = ""
                stats.sort(key=itemgetter('bossWinRate'), reverse=True)
                for counter, br in enumerate(stats[:10], start=1):
                    name = None
                    for b in brawlers:
                        if b['id'] == br['brawler']:
                            name = b['name'].upper()
                            break
                    if name is None:
                        continue                               
                    bwr += f"{get_brawler_emoji(name)} `{int(br['bossWinRate'])}%` "
                    if counter % 5 == 0:
                        bwr += "\n"
                embed.add_field(name="Best Boss Win Rates", value=bwr, inline=False)

            if len(stats) > 0 and 'useRate' in stats[0]:
                ur = ""
                stats.sort(key=itemgetter('useRate'), reverse=True)
                for counter, br in enumerate(stats[:10], start=1):
                    name = None
                    for b in brawlers:
                        if b['id'] == br['brawler']:
                            name = b['name'].upper()
                            break
                    if name is None:
                        continue                               
                    ur += f"{get_brawler_emoji(name)} `{int(br['useRate'])}%` "
                    if counter % 5 == 0:
                        ur += "\n"
                embed.add_field(name="Highest Use Rates", value=ur, inline=False)
                                            
        if result_map['disabled']:
            embed.description = "This map is currently disabled."
        embed.set_footer(text="Data provided by starlist.pro")
        embed.set_image(url=result_map['url'])
        await ctx.send(embed=embed)
       
    def get_badge(self, badge_id):
        guild = self.bot.get_guild(717766786019360769)
        em = discord.utils.get(guild.emojis, name=str(badge_id-8000000).rjust(2, "0"))
        return str(em)
                                   
    @commands.command()
    async def lblink(self, ctx, *, member: Union[discord.Member, str] = None):
        """Get LA clubs website leaderboard link"""
        await ctx.trigger_typing()
        prefix = ctx.prefix
        tag = ""

        member = ctx.author if member is None else member

        if isinstance(member, discord.Member):
            tag = await self.config.user(member).tag()
            if tag is None:
                return await ctx.send(embed=badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))
        elif member.startswith("#"):
            tag = member.upper().replace('O', '0')
        else:
            try:
                member = self.bot.get_user(int(member))
                if member is not None:
                    tag = await self.config.user(member).tag()
                    if tag is None:
                        return await ctx.send(embed=badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))
            except ValueError:
                member = discord.utils.get(ctx.guild.members, name=member)
                if member is not None:
                    tag = await self.config.user(member).tag()
                    if tag is None:
                        return await ctx.send(embed=badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))
                                            
        return await ctx.send(f"https://laclubs.net/lb#{tag.strip('#')}")                    
                                            
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
                await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

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
                await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))
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
            await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))
            return

        if keyword is None:
            url = f"https://laclubs.net/club?tag={club.tag.strip('#').upper()}"
            if club.description is not None:
                embed = discord.Embed(description=f"```{discord.utils.escape_markdown(club.description)}```")
            else:
                embed = discord.Embed(description="```None```")
            embed.set_author(name=f"{club.name} {club.tag}", icon_url=f"https://cdn.starlist.pro/club/{club.raw_data['badgeId']}.png?v=1", url=url)
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
                value=f"<:icon_gameroom:553299647729238016> {len(club.members)}/100")
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
            else:
                startingembed.add_field(name=f"Vice Presidents: {vp_count}", value=vp_value, inline=False)
            if senior_value == "":
                startingembed.add_field(name=f"Seniors: {senior_count}", value="None", inline=False)
            elif len(senior_value) > 1024:
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
            url = "https://api.starlist.pro/clublog/" + club.tag.replace("#", "")
            log = await self.starlist_request(url)
            if log['status'] == "trackingDisabled":
                return await ctx.send(embed=badEmbed(f"Tracking for this club isn't enabled on starlist.pro website!"))
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
            embed.set_footer(text="Data provided by starlist.pro")

            await ctx.send(embed=embed)
        elif keyword == "link":
            return await ctx.send(f"https://laclubs.net/club?tag={club.tag.strip('#').upper()}")                    
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

        if len((await self.config.guild(ctx.guild).clubs()).keys()) < 1:
            return await ctx.send(
                embed=badEmbed(f"This server has no clubs saved. Save a club by using {ctx.prefix}clubs add!"))

        loadingembed = discord.Embed(colour=discord.Colour.red(),
                                     description="Requesting clubs. Might take a while.\n(0%)", title="Loading...")
        msg = await ctx.send(embed=loadingembed)

        saved_clubs = await self.config.guild(ctx.guild).clubs()

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
                if not offline:
                    if 0 <= ind / len(keys) <= 0.25:
                        if loadingembed.description != "Requesting clubs. Might take a while.\n(25%) ────":
                            loadingembed = discord.Embed(colour=discord.Colour.red(),
                                                            description="Requesting clubs. Might take a while.\n(25%) ────",
                                                            title="Loading...")
                            await msg.edit(embed=loadingembed)
                    elif 0.25 <= ind / len(keys) <= 0.5:
                        if loadingembed.description != "Requesting clubs. Might take a while.\n(50%) ────────":
                            loadingembed = discord.Embed(colour=discord.Colour.red(),
                                                            description="Requesting clubs. Might take a while.\n(50%) ────────",
                                                            title="Loading...")
                            await msg.edit(embed=loadingembed)
                    elif 0.5 <= ind / len(keys) <= 0.75:
                        if loadingembed.description != "Requesting clubs. Might take a while.\n(75%) ────────────":
                            loadingembed = discord.Embed(colour=discord.Colour.red(),
                                                            description="Requesting clubs. Might take a while.\n(75%) ────────────",
                                                            title="Loading...")
                            await msg.edit(embed=loadingembed)
                    elif 0.75 <= ind / len(keys) <= 1:
                        if loadingembed.description != "Requesting clubs. Might take a while.\n(100%) ────────────────":
                            loadingembed = discord.Embed(colour=discord.Colour.red(),
                                                            description="Requesting clubs. Might take a while.\n(100%) ────────────────",
                                                            title="Loading...")
                            await msg.edit(embed=loadingembed)
                #await asyncio.sleep(0.3)

            embedFields = []

            loadingembed = discord.Embed(colour=discord.Colour.red(), description="Almost there!", title="Creating the embed...")
            if not offline:
                await msg.edit(embed=loadingembed)
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
                                  
                    url = f"https://laclubs.net/club?tag={clubs[i].tag.strip('#').upper()}"

                    if low_clubs and len(clubs[i].members) >= 95:
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
                    e_value += f"`{clubs[i].required_trophies}+` <:icon_gameroom:553299647729238016>`{len(clubs[i].members)}` [🔗]({url})"
                    embedFields.append([e_name, e_value])

                await self.config.guild(ctx.guild).set_raw("clubs", value=saved_clubs)

            else:
                await msg.edit(embed=loadingembed)
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
                                  
                    url = f"https://laclubs.net/club?tag={ctag.strip('#').upper()}"
                                           
                    if low_clubs and cmembers >= 95:
                        continue

                    if membersforhawk:
                        if len(clubs[i].members) != membersnumber:
                            continue

                    if trophy_range:
                        if creq > trange:
                            continue

                    e_name = f"{badge_emoji} {cname} [{ckey}] #{ctag} {cinfo}"
                    e_value = f"{club_status[ctype.lower()]['emoji']} <:bstrophy:552558722770141204>`{cscore}` {get_league_emoji(creq)}`{creq}+` <:icon_gameroom:553299647729238016>`{cmembers}` [🔗]({url})"
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
                footer = f"[{page}/{len(embedFields)//8+1}] API is offline, showing last saved data." if offline else f"[{page}/{len(embedFields)//8+1}] Need more info about a club? Use {ctx.prefix}club [key]"
                embed.set_footer(text=footer)
                for e in embedFields[i:i + 8]:
                    embed.add_field(name=e[0], value=e[1], inline=False)
                embedsToSend.append(embed)

            if len(embedsToSend) > 1:
                await msg.delete()
                await menu(ctx, embedsToSend, {"⬅": prev_page, "➡": next_page}, timeout=2000)
            elif len(embedsToSend) == 1:
                await msg.delete()
                await ctx.send(embed=embedsToSend[0])
            else:
                await msg.delete()
                await ctx.send("No clubs found!")

        except ZeroDivisionError as e:
            return await ctx.send(
                "**Something went wrong, please send a personal message to LA Modmail bot or try again!**")

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
            return await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!**")

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

    @commands.cooldown(1, 20, commands.BucketType.user)
    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def whitelistbs(self, ctx):
        """Show whitelists' clubs"""
        if ctx.guild.id != 401883208511389716:
            return await ctx.send("This command can only be used in LA Gaming - Brawl Stars.")

        await ctx.trigger_typing()

        whitelist = ctx.guild.get_role(693659561747546142)

        messages = []
        msg = ""
        for member in ctx.guild.members:
            if whitelist not in member.roles:
                continue
            tag = await self.config.user(member).tag()
            alt = await self.config.user(member).alt()
            if tag is None:
                msg += f"**{member.name}**: has no tag saved.\n"
            try:
                player = await self.ofcbsapi.get_player(tag)
                if alt is not None:
                    playeralt = await self.ofcbsapi.get_player(alt)
                await asyncio.sleep(0.2)
            except brawlstats.errors.RequestError:
                msg += f"**{member.name}**: request error.\n"
                continue
            except Exception as e:
                msg += "Something went wrong."
                return
            player_in_club = "name" in player.raw_data["club"]
            if alt is not None:
                player_in_club2 = "name" in playeralt.raw_data["club"]
            if len(msg) > 1800:
                messages.append(msg)
                msg = ""
            if player_in_club:
                clubobj = await self.ofcbsapi.get_club(player.club.tag)
                msg += f"**{str(member)}** `{player.trophies}` <:bstrophy:552558722770141204>: {player.club.name} ({len(clubobj.members)}/100)\n"
            else:
                msg += f"**{str(member)}** `{player.trophies}` <:bstrophy:552558722770141204>: not in a club.\n"
            if alt is not None:
                if player_in_club2:
                    clubobj = await self.ofcbsapi.get_club(playeralt.club.tag)
                    msg += f"**{str(member)}'s alt** `{playeralt.trophies}` <:bstrophy:552558722770141204>: {playeralt.club.name} ({len(clubobj.members)}/100)\n"
                else:
                    msg += f"**{str(member)}'s alt** `{playeralt.trophies}` <:bstrophy:552558722770141204>: not in a club.\n"
        if len(msg) > 0:
            messages.append(msg)
        for m in messages:
            await ctx.send(embed=discord.Embed(colour=discord.Colour.green(), description=m))

    @commands.cooldown(1, 20, commands.BucketType.user)
    @commands.guild_only()
    @whitelistbs.command(name="stats")
    async def whiteliststats(self, ctx):
        """Show general whitelists' stats"""
        if ctx.guild.id != 401883208511389716:
            return await ctx.send("This command can only be used in LA Gaming - Brawl Stars.")

        await ctx.trigger_typing()

        whitelist = ctx.guild.get_role(693659561747546142)

        clubs = {}
        for member in ctx.guild.members:
            if whitelist not in member.roles:
                continue
            tag = await self.config.user(member).tag()
            alt = await self.config.user(member).alt()
            if tag is None:
                continue
            try:
                player = await self.ofcbsapi.get_player(tag)
                if alt is not None:
                    playeralt = await self.ofcbsapi.get_player(alt)
                await asyncio.sleep(0.2)
            except brawlstats.errors.RequestError:
                continue
            except Exception as e:
                return
            player_in_club = "name" in player.raw_data["club"]
            if alt is not None:
                player_in_club2 = "name" in playeralt.raw_data["club"]
            if player_in_club:
                try:
                    current = clubs[player.club.name]
                    clubs[player.club.name] = current + 1
                except KeyError:
                    clubs[player.club.name] = 1
            else:
                try:
                    current = clubs["No club"]
                    clubs["No club"] = current + 1
                except KeyError:
                    clubs["No club"] = 1
            if alt is not None:
                if player_in_club2:
                    try:
                        current = clubs[playeralt.club.name]
                        clubs[playeralt.club.name] = current + 1
                    except KeyError:
                        clubs[playeralt.club.name] = 1
                else:
                    try:
                        current = clubs["No club"]
                        clubs["No club"] = current + 1
                    except KeyError:
                        clubs["No club"] = 1

        messages = []
        msg = ""

        for club, count in clubs.items():
            if len(msg) > 1800:
                messages.append(msg)
                msg = ""
            if club.startswith("LA") or club == "No club":
                msg = msg + f"<:bstrophy:552558722770141204> **{club}**: {count}\n"
            else:
                msg = msg + f"<:bstrophy:552558722770141204> **{club}**: {count}, doesn't look like an LA club\n"

        if len(msg) > 0:
            messages.append(msg)
        for m in messages:
            await ctx.send(embed=discord.Embed(colour=discord.Colour.green(), description=m))

    @commands.cooldown(1, 20, commands.BucketType.user)
    @commands.guild_only()
    @whitelistbs.command(name="club")
    async def whitelistclub(self, ctx, clubtag):
        """Show whitelist members in a certain club"""
        if ctx.guild.id != 401883208511389716:
            return await ctx.send("This command can only be used in LA Gaming - Brawl Stars.")

        await ctx.trigger_typing()

        if "#" not in clubtag:
            clubtag = "#" + clubtag

        clubtag = clubtag.strip().upper()

        whitelist = ctx.guild.get_role(693659561747546142)

        club = await self.ofcbsapi.get_club(clubtag)

        msg = ""
        for member in ctx.guild.members:
            if whitelist not in member.roles:
                continue
            tag = await self.config.user(member).tag()
            alt = await self.config.user(member).alt()
            if tag is None:
                continue
            for m in club.members:
                if m.tag == "#" + tag.upper():
                    msg += f"**{str(member)}** `{m.trophies}` {m.name}\n"
                if alt is not None:
                    if m.tag == "#" + alt.upper():
                            msg += f"**{str(member)}'s alt** `{m.trophies}` {m.name}\n"

        if msg != "":
            await ctx.send(embed=discord.Embed(colour=discord.Colour.green(), description=msg))
        else:
            await ctx.send(embed=badEmbed("Looks like no one's in this club."))

    @commands.cooldown(1, 20, commands.BucketType.user)
    @commands.command()
    async def trophylb(self, ctx):
        await ctx.send("Looks like this command was deleted. Refer to https://laclubs.net/lb for an up-to-date trophy leaderboard!")

