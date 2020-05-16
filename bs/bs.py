import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.embed import randomize_colour
from redbot.core.utils.menus import menu, prev_page, next_page
from discord.ext import tasks

from .utils import badEmbed, goodEmbed, get_league_emoji, get_rank_emoji, get_brawler_emoji, remove_codes

from random import choice
import asyncio
import brawlstats
from typing import Union
from re import sub
import datetime


class BrawlStarsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=5245652)
        default_user = {"tag": None}
        self.config.register_user(**default_user)
        default_guild = {"clubs": {}}
        self.config.register_guild(**default_guild)
        self.sortroles.start()
        self.sortrolesasia.start()
        self.sortrolesbd.start()
        self.sortrolesspain.start()

    def cog_unload(self):
        self.sortroles.cancel()
        self.sortrolesasia.cancel()
        self.sortrolesbd.cancel()
        self.sortrolesspain.cancel()

    async def initialize(self):
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError(
                "The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.Client(
            ofcbsapikey["api_key"], is_async=True)
        
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.channel.id == 680113859759308910 and msg.author.id != 599286708911210557:
            try:
                id = int(msg.content)
                user = self.bot.get_user(int(msg.content))
                if user is None:
                    await (self.bot.get_channel(680113859759308910)).send(".")
                tag = await self.config.user(user).tag()
                if tag is None:
                    await (self.bot.get_channel(680113859759308910)).send(".")
                else:
                    await (self.bot.get_channel(680113859759308910)).send(tag.upper())
            except ValueError:
                pass

    @commands.command(aliases=['bssave'])
    async def save(self, ctx, tag, member: discord.Member = None):
        """Save your Brawl Stars player tag"""
        member = ctx.author if member is None else member

        tag = tag.lower().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        try:
            player = await self.ofcbsapi.get_player(tag)
            await self.config.user(member).tag.set(tag.replace("#", ""))
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
    async def renamebs(self, ctx, member: discord.Member = None):
        """Change a name of a user to be nickname|club_name"""
        await ctx.trigger_typing()
        prefix = ctx.prefix
        member = ctx.author if member is None else member

        tag = await self.config.user(member).tag()
        if tag is None:
            return await ctx.send(embed=badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))

        player = await self.ofcbsapi.get_player(tag)
        if "name" in player.raw_data["club"]:
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

    @commands.command(aliases=['p', 'bsp', 'stats'])
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
            desc = "/p\n/bsprofile @user\n/p discord_name\n/p discord_id\n/p #CRTAG"
            embed = discord.Embed(
                title="Invalid argument!",
                colour=discord.Colour.red(),
                description=desc)
            return await ctx.send(embed=embed)
        try:
            player = await self.ofcbsapi.get_player(tag)

        except brawlstats.errors.NotFoundError:
            return await ctx.send(embed=badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send("****Something went wrong, please send a personal message to LA Modmail bot or try again!****")

        colour = player.name_color if player.name_color is not None else "0xffffffff"
        embed = discord.Embed(color=discord.Colour.from_rgb(
            int(colour[4:6], 16), int(colour[6:8], 16), int(colour[8:10], 16)))
        embed.set_author(
            name=f"{player.name} {player.raw_data['tag']}",
            icon_url=member.avatar_url if isinstance(member, discord.Member) else "https://i.imgur.com/ZwIP41S.png")
        embed.add_field(
            name="Trophies",
            value=f"{get_league_emoji(player.trophies)} {player.trophies}")
        embed.add_field(
            name="Highest Trophies",
            value=f"<:totaltrophies:614517396111097866> {player.highest_trophies}")
        embed.add_field(
            name="Level",
            value=f"<:exp:614517287809974405> {player.exp_level}")
        embed.add_field(
            name="Unlocked Brawlers",
            value=f"<:brawlers:614518101983232020> {len(player.brawlers)}")
        if "tag" in player.raw_data["club"]:
            embed.add_field(
                name="Club",
                value=f"<:bsband:600741378497970177> {player.club.name}")
            try:
                club = await self.ofcbsapi.get_club(player.club.tag)
                for m in club.members:
                    if m.tag == player.raw_data['tag']:
                        embed.add_field(name="Role", value=f"<:role:614520101621989435> {m.role.capitalize()}")
                        break
            except brawlstats.errors.RequestError:
                embed.add_field(
                    name="Role",
                    value=f"<:offline:642094554019004416> Error while retrieving role")
        else:
            embed.add_field(
                name="Club",
                value=f"<:noclub:661285120287834122> Not in a club")
        embed.add_field(
            name="3v3 Wins",
            value=f"<:3v3:614519914815815693> {player.raw_data['3vs3Victories']}")
        embed.add_field(
            name="Solo SD Wins",
            value=f"<:sd:614517124219666453> {player.solo_victories}")
        embed.add_field(
            name="Duo SD Wins",
            value=f"<:duosd:614517166997372972> {player.duo_victories}")
        #embed.add_field(
        #    name="Best Time in Robo Rumble",
        #    value=f"<:roborumble:614516967092781076> {player.best_robo_rumble_time//60}:{str(player.best_robo_rumble_time%60).rjust(2, '0')}")
        #embed.add_field(
        #    name="Best Time as Big Brawler",
        #    value=f"<:biggame:614517022323245056> {player.best_time_as_big_brawler//60}:{str(player.best_time_as_big_brawler%60).rjust(2, '0')}")
        if "powerPlayPoints" in player.raw_data:
            embed.add_field(
                name="Power Play Points",
                value=f"<:powertrophies:661266876235513867> {player.raw_data['powerPlayPoints']}")
        else:
            embed.add_field(name="Power Play Points",
                            value=f"<:powertrophies:661266876235513867> 0")
        if "highestPowerPlayPoints" in player.raw_data:
            embed.add_field(
                name="Highest PP Points",
                value=f"<:powertrophies:661266876235513867> {player.raw_data['highestPowerPlayPoints']}")
        #embed.add_field(
        #    name="Qualified For Championship",
        #    value=f"<:powertrophies:661266876235513867> {player.raw_data['isQualifiedFromChampionshipChallenge']}")
        texts = [
            "Check out all your brawlers using /brawlers!", 
            "Want to see your club stats? Try /club!", 
            "Have you seen all our clubs? No? Do /clubs!",
            "You can see stats of other players by typing /p @user.",
            "You can display player's stats by using his tag! /p #TAGHERE",
            "Did you know LA Bot can display CR stats as well? /crp"
        ]
        embed.set_footer(text=choice(texts))
        await ctx.send(embed=embed)

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
            desc = "/p\n/bsprofile @user\n/p discord_name\n/p discord_id\n/p #CRTAG"
            embed = discord.Embed(
                title="Invalid argument!",
                colour=discord.Colour.red(),
                description=desc)
            return await ctx.send(embed=embed)
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

        brawlers = []
        messages = []
        for brawler in player.raw_data['brawlers']:
            pair = []
            pair.append(brawler.get('name'))
            pair.append(brawler.get('trophies'))
            brawlers.append(pair)
        brawlers = sorted(brawlers, key=lambda x: x[1], reverse=True)
        brawlersmsg = ""
        for brawler in brawlers:
            if len(brawlersmsg) > 1800:
                messages.append(brawlersmsg)
                brawlersmsg = ""
            brawlersmsg += (
                f"{get_brawler_emoji(brawler[0])} **{brawler[0].lower().capitalize()}**: {brawler[1]} <:bstrophy:552558722770141204>\n")
        if len(brawlersmsg) > 0:
            messages.append(brawlersmsg)
        messages[0] = f"**Brawlers({len(brawlers)}\\37):**\n" + messages[0]
        for i in range(len(messages)):
            embed = discord.Embed(description=messages[i], color=discord.Colour.from_rgb(int(colour[4:6], 16), int(colour[6:8], 16), int(colour[8:10], 16)))
            if i == 0:
                embed.set_author(
                    name=f"{player.name} {player.raw_data['tag']}",
                    icon_url=member.avatar_url if isinstance(member, discord.Member) else "https://i.imgur.com/ZwIP41S.png")
            if i == len(messages)-1:
                embed.set_footer(text="/brawler name for more stats")
            await ctx.send(embed=embed)

    @commands.command()
    async def brawler(self, ctx, brawler: str, member: discord.Member = None):
        """Brawler specific info"""
        await ctx.trigger_typing()
        prefix = ctx.prefix

        if member is None:
            member = ctx.author

        tag = await self.config.user(member).tag()
        if tag is None:
            return await ctx.send(embed=badEmbed(f"You have no tag saved! Use {prefix}bssave <tag>"))

        if tag is None or tag == "":
            desc = "/p\n/bsprofile @user\n/p discord_name\n/p discord_id\n/p #CRTAG"
            embed = discord.Embed(
                title="Invalid argument!",
                colour=discord.Colour.red(),
                description=desc)
            return await ctx.send(embed=embed)
        try:
            player = await self.ofcbsapi.get_player(tag)

        except brawlstats.errors.NotFoundError:
            return await ctx.send(embed=badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send(
                "****Something went wrong, please send a personal message to LA Modmail bot or try again!****")

        br = None
        for b in player.raw_data['brawlers']:
            if b.get('name') == brawler.upper():
                br = b
        if br is None:
            return await ctx.send(embed=badEmbed(f"There's no such brawler!"))

        colour = player.name_color if player.name_color is not None else "0xffffffff"
        embed = discord.Embed(color=discord.Colour.from_rgb(
            int(colour[4:6], 16), int(colour[6:8], 16), int(colour[8:10], 16)))
        embed.set_author(
            name=f"{player.name} {player.raw_data['tag']}",
            icon_url=member.avatar_url if isinstance(member, discord.Member) else "https://i.imgur.com/ZwIP41S.png")
        embed.add_field(
            name="Brawler",
            value=f"{get_brawler_emoji(brawler.upper())} {brawler.lower().capitalize()}")
        embed.add_field(
            name="Trophies",
            value=f"<:bstrophy:552558722770141204> {br.get('trophies')}")
        embed.add_field(
            name="Highest Trophies",
            value=f"{get_rank_emoji(br.get('rank'))} {br.get('highestTrophies')}")
        embed.add_field(name="Power Level",
                        value=f"<:pp:664267845336825906> {br.get('power')}")
        starpowers = ""
        for star in br.get('starPowers'):
            starpowers += f"<:starpower:664267686720700456> {star.get('name')}\n"
        if starpowers != "":
            embed.add_field(name="Star Powers", value=starpowers)
        else:
            embed.add_field(name="Star Powers",
                            value="<:starpower:664267686720700456> None")
        await ctx.send(embed=embed)

    @commands.command()
    async def club(self, ctx, key: Union[discord.Member, str] = None):
        """View players club or club saved in a server"""
        await ctx.trigger_typing()
        if key is None:
            mtag = await self.config.user(ctx.author).tag()
            if mtag is None:
                return await ctx.send(embed=badEmbed(f"You have no tag saved! Use {ctx.prefix}bssave <tag>"))
            try:
                player = await self.ofcbsapi.get_player(mtag)
                if not player.club.tag:
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
                if not player.club.tag:
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

        if club.description is not None:
            embed = discord.Embed(description=f"```{remove_codes(club.description)}```")
        else:
            embed = discord.Embed(description="```None```")
        embed.set_author(name=f"{club.name} {club.tag}")
        embed.add_field(
            name="Total Trophies",
            value=f"<:bstrophy:552558722770141204> `{club.trophies}`")
        embed.add_field(
            name="Required Trophies",
            value=f"{get_league_emoji(club.required_trophies)} `{club.required_trophies}`")
        embed.add_field(
            name="Average Trophies",
            value=f"<:bstrophy:552558722770141204> `{club.trophies//len(club.members)}`")
        for m in club.members:
            if m.role == "president":
                embed.add_field(
                    name="President",
                    value=f"{get_league_emoji(m.trophies)}`{m.trophies}` {m.name}")
                break
        embed.add_field(
            name="Members",
            value=f"<:icon_gameroom:553299647729238016> {len(club.members)}/100")
        embed.add_field(
            name="Status",
            value=f"<:bslock:552560387279814690> {club.type.title()}")
        topm = ""
        for i in range(5):
            try:
                topm += f"{get_league_emoji(club.members[i].trophies)}`{club.members[i].trophies}` {remove_codes(club.members[i].name)}\n"
            except IndexError:
                pass
        worstm = ""
        for i in range(5):
            try:
                worstm += f"{get_league_emoji(club.members[len(club.members)-5+i].trophies)}`{club.members[len(club.members)-5+i].trophies}` {remove_codes(club.members[len(club.members)-5+i].name)}\n"
            except IndexError:
                pass
        embed.add_field(name="Top Members", value=topm, inline=True)
        embed.add_field(name="Lowest Members", value=worstm, inline=True)
        return await ctx.send(embed=randomize_colour(embed))

    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def clubs(self, ctx, key: str = None):
        """View all clubs saved in a server"""
        offline = False
        await ctx.trigger_typing()
        if key == "forceoffline":
            offline = True
            key = None

        if len((await self.config.guild(ctx.guild).clubs()).keys()) < 1:
            return await ctx.send(
                embed=badEmbed(f"This server has no clubs saved. Save a club by using {ctx.prefix}clubs add!"))

        loadingembed = discord.Embed(colour=discord.Colour.red(), description="Requesting clubs. Might take a while.\n(0%)", title="Loading...")
        msg = await ctx.send(embed=loadingembed)
        try:
            try:
                clubs = []
                keys = (await self.config.guild(ctx.guild).clubs()).keys()
                for ind, key in enumerate(keys):
                    club = await self.ofcbsapi.get_club(await self.config.guild(ctx.guild).clubs.get_raw(key, "tag"))
                    if 0 <= ind / len(keys) <= 0.25:
                        if loadingembed.description != "Requesting clubs. Might take a while.\n(25%) ────":
                            loadingembed = discord.Embed(colour=discord.Colour.red(), description="Requesting clubs. Might take a while.\n(25%) ────", title="Loading...")
                            await msg.edit(embed=loadingembed)
                    elif 0.25 <= ind / len(keys) <= 0.5:
                        if loadingembed.description != "Requesting clubs. Might take a while.\n(50%) ────────":
                            loadingembed = discord.Embed(colour=discord.Colour.red(), description="Requesting clubs. Might take a while.\n(50%) ────────", title="Loading...")
                            await msg.edit(embed=loadingembed)
                    elif 0.5 <= ind / len(keys) <= 0.75:
                        if loadingembed.description != "Requesting clubs. Might take a while.\n(75%) ────────────":
                            loadingembed = discord.Embed(colour=discord.Colour.red(), description="Requesting clubs. Might take a while.\n(75%) ────────────", title="Loading...")
                            await msg.edit(embed=loadingembed)
                    elif 0.75 <= ind / len(keys) <= 1:
                        if loadingembed.description != "Requesting clubs. Might take a while.\n(100%) ────────────────":
                            loadingembed = discord.Embed(colour=discord.Colour.red(), description="Requesting clubs. Might take a while.\n(100%) ────────────────", title="Loading...")
                            await msg.edit(embed=loadingembed)
                    clubs.append(club)
                    # await asyncio.sleep(1)
            except brawlstats.errors.RequestError as e:
                offline = True

            embedFields = []

            if not offline:
                loadingembed = discord.Embed(colour=discord.Colour.red(),
                                             description="Almost there.",
                                             title="Creating the embed...")
                await msg.edit(embed=loadingembed)
                clubs = sorted(clubs, key=lambda sort: (
                    sort.trophies), reverse=True)

                for i in range(len(clubs)):
                    key = ""
                    for k in (await self.config.guild(ctx.guild).clubs()).keys():
                        if clubs[i].tag.replace("#", "") == await self.config.guild(ctx.guild).clubs.get_raw(k, "tag"):
                            key = k

                    await self.config.guild(ctx.guild).clubs.set_raw(key, 'lastMemberCount', value=len(clubs[i].members))
                    await self.config.guild(ctx.guild).clubs.set_raw(key, 'lastRequirement', value=clubs[i].required_trophies)
                    await self.config.guild(ctx.guild).clubs.set_raw(key, 'lastScore', value=clubs[i].trophies)
                    await self.config.guild(ctx.guild).clubs.set_raw(key, 'lastPosition', value=i)

                    info = await self.config.guild(ctx.guild).clubs.get_raw(key, "info", default="")
                    e_name = f"<:bsband:600741378497970177> {clubs[i].name} [{key}] {clubs[i].tag} {info}"
                    e_value = f"<:bstrophy:552558722770141204>`{clubs[i].trophies}` {get_league_emoji(clubs[i].required_trophies)}`{clubs[i].required_trophies}+` <:icon_gameroom:553299647729238016>`{len(clubs[i].members)}`"
                    embedFields.append([e_name, e_value])

            else:
                loadingembed = discord.Embed(colour=discord.Colour.red(),
                                             description="Almost there.",
                                             title="Creating the embed...")
                await msg.edit(embed=loadingembed)
                offclubs = []
                for k in (await self.config.guild(ctx.guild).clubs()).keys():
                    offclubs.append([await self.config.guild(ctx.guild).clubs.get_raw(k, "lastPosition"), k])
                offclubs = sorted(offclubs, key=lambda x: x[0])

                for club in offclubs:
                    ckey = club[1]
                    cscore = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "lastScore")
                    cname = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "name")
                    ctag = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "tag")
                    cinfo = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "info")
                    cmembers = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "lastMemberCount")
                    creq = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "lastRequirement")
                        
                    e_name = f"<:bsband:600741378497970177> {cname} [{ckey}] #{ctag} {cinfo}"
                    e_value = f"<:bstrophy:552558722770141204>`{cscore}` {get_league_emoji(creq)}`{creq}+` <:icon_gameroom:553299647729238016>`{cmembers}` "
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
                footer = "<:offline:642094554019004416> API is offline, showing last saved data." if offline else f"Need more info about a club? Use {ctx.prefix}club [key]"
                embed.set_footer(text=footer)
                for e in embedFields[i:i + 8]:
                    embed.add_field(name=e[0], value=e[1], inline=False)
                embedsToSend.append(embed)

            if len(embedsToSend) > 1:
                await msg.delete()
                await menu(ctx, embedsToSend, {"⬅": prev_page, "➡": next_page, }, timeout=2000)
            else:
                await msg.delete()
                await ctx.send(embed=embedsToSend[0])

        except ZeroDivisionError as e:
            return await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!**")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @clubs.command(name="add")
    async def clans_add(self, ctx, key: str, tag: str):
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
                "info": ""
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
        try:
            await self.config.guild(ctx.guild).clubs.set_raw(key, "info", value=info)
            await ctx.send(embed=goodEmbed("Club info successfully edited!"))
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

    @tasks.loop(hours=4)
    async def sortroles(self):
        ch = self.bot.get_channel(653295573872672810)
        await ch.trigger_typing()
        labs = ch.guild.get_role(576028728052809728)
        guest = ch.guild.get_role(578260960981286923)
        newcomer = ch.guild.get_role(534461445656543255)
        brawlstars = ch.guild.get_role(576002604740378629)
        vp = ch.guild.get_role(536993652648574976)
        pres = ch.guild.get_role(536993632918568991)
        error_counter = 0

        for member in ch.guild.members:
            if member.bot:
                continue
            tag = await self.config.user(member).tag()
            if tag is None:
                msg = ""
                if pres in member.roles or vp in member.roles:
                    msg += "Has President or VP role, no tag saved.\n"
                    msg += await self.removeroleifpresent(member, vp, pres)
                    try:
                        await member.send(f"Hello {member.mention},\nyour (Vice)President role in LA Brawl Stars server has been removed.\nThe reason is you don't have your in-game tag saved at LA bot. You can fix it by saving your tag using `/save #YOURTAG`.\n")
                    except (discord.HTTPException, discord.Forbidden) as e:
                        msg += f"Couldn't send a DM with info. {str(e)}\n"
                    await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=msg, title=str(member), timestamp=datetime.datetime.now()))
                continue
            try:
                player = await self.ofcbsapi.get_player(tag)
                await asyncio.sleep(0.2)
            except brawlstats.errors.RequestError as e:
                await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=f"{str(member)} ({member.id}) #{tag}"))
                error_counter += 1 
                if error_counter == 5:
                    await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=f"Stopping after 5 request errors! Displaying the last one:\n({str(e)})"))
                    break
                await asyncio.sleep(1)
                continue
            except Exception as e:
                return await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=f"**Something went wrong while requesting {tag}!**\n({str(e)})"))

            msg = ""
            player_in_club = "name" in player.raw_data["club"]
            member_roles = []
            member_role = None
            member_role_expected = None

            for role in member.roles:
                if role.name.startswith('LA '):
                    member_roles.append(role)

            if len(member_roles) > 1:
                msg += f"Found more than one club role. (**{', '.join([str(r) for r in member_roles])}**)\n"
                for role in member_roles:
                    if sub(r'[^\x00-\x7f]', r'', role.name).strip() != sub(r'[^\x00-\x7f]', r'', player.club.name).strip():
                        msg += await self.removeroleifpresent(member, role)
            
            member_role = None if len(member_roles) < 1 else member_roles[0]

            if not player_in_club:
                msg += await self.removeroleifpresent(member, labs, vp, pres, newcomer)
                msg += await self.addroleifnotpresent(member, guest)
                if member_role is not None:
                    msg += await self.removeroleifpresent(member, member_role)

            if player_in_club and not player.club.name.startswith("LA "):
                msg += await self.removeroleifpresent(member, labs, vp, pres, newcomer, member_role)
                msg += await self.addroleifnotpresent(member, guest, brawlstars)

            if player_in_club and player.club.name.startswith("LA "):
                for role in ch.guild.roles:
                    if sub(r'[^\x00-\x7f]', r'', role.name).strip() == sub(r'[^\x00-\x7f]', r'', player.club.name).strip():
                        member_role_expected = role
                        break
                if member_role_expected is None:
                    await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=f"Role for the club {player.club.name} not found.", title=str(member), timestamp=datetime.datetime.now()))
                    continue
                msg += await self.removeroleifpresent(member, guest, newcomer)
                msg += await self.addroleifnotpresent(member, labs, brawlstars)
                if member_role is None:
                    msg += await self.addroleifnotpresent(member, member_role_expected)
                elif member_role != member_role_expected:
                    msg += await self.removeroleifpresent(member, member_role)
                    msg += await self.addroleifnotpresent(member, member_role_expected)
                try:
                    await asyncio.sleep(0.2)
                    player_club = await self.ofcbsapi.get_club(player.club.tag)
                    for mem in player_club.members:
                        if mem.tag == player.raw_data['tag']:
                            if mem.role.lower() == 'vicepresident':
                                msg += await self.addroleifnotpresent(member, vp)
                                msg += await self.removeroleifpresent(member, pres)
                            elif mem.role.lower() == 'president':
                                msg += await self.addroleifnotpresent(member, pres)
                                msg += await self.removeroleifpresent(member, vp)
                            elif mem.role.lower() == 'member':
                                msg += await self.removeroleifpresent(member, vp, pres)
                            break
                except brawlstats.errors.RequestError:
                    pass
            if msg != "":
                await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg, title=str(member), timestamp=datetime.datetime.now()))

    @sortroles.before_loop
    async def before_sortroles(self):
        await asyncio.sleep(5)

    @tasks.loop(hours=5)
    async def sortrolesasia(self):
        ch = self.bot.get_channel(672267298001911838)
        await ch.trigger_typing()
        lafamily = ch.guild.get_role(663795352666636305)
        guest = ch.guild.get_role(663798304194166854)
        newcomer = ch.guild.get_role(663799853889093652)
        vp = ch.guild.get_role(663793699972579329)
        pres = ch.guild.get_role(663793444199596032)
        leadership = ch.guild.get_role(663910848569409598)
        leadershipemb = ch.guild.get_role(673177525396176927)
        error_counter = 0

        for member in ch.guild.members:
            if member.bot:
                continue
            tag = await self.config.user(member).tag()
            if tag is None:
                continue
            try:
                player = await self.ofcbsapi.get_player(tag)
                await asyncio.sleep(0.5)
            except brawlstats.errors.RequestError as e:
                error_counter += 1
                if error_counter == 20:
                    await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=f"Stopping after 20 request errors! Displaying the last one:\n({str(e)})"))
                    break
                await asyncio.sleep(1)
                continue
            except Exception as e:
                return await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=f"**Something went wrong while requesting {tag}!**\n({str(e)})"))

            msg = ""
            player_in_club = "name" in player.raw_data["club"]
            member_roles = []
            member_role = None
            member_role_expected = None
            tags = []
            guilds = await self.config.all_guilds()
            asia = guilds[663716223258984496]
            clubs = asia["clubs"]
            for club in clubs:
                info = clubs[club]
                tag = "#" + info["tag"]
                tags.append(tag)

            for role in member.roles:
                if role.name.startswith('LA ') and role.id != 682056906222993446:
                    member_roles.append(role)

            if len(member_roles) > 1:
                msg += f"**{str(member)}** has more than one club role. Removing **{', '.join([str(r) for r in member_roles])}**"
                member_role = member_roles[0]
                for role in member_roles[1:]:
                    msg += await self.removeroleifpresent(member, role)

            member_role = None if len(member_roles) < 1 else member_roles[0]

            if not player_in_club:
                msg += await self.removeroleifpresent(member, lafamily, vp, pres, newcomer)
                msg += await self.addroleifnotpresent(member, guest)
                if member_role is not None:
                    msg += await self.removeroleifpresent(member, member_role)

            if player_in_club and player.club.tag not in tags:
                msg += await self.removeroleifpresent(member, lafamily, vp, pres, newcomer, leadership, leadershipemb)
                msg += await self.addroleifnotpresent(member, guest)
                if member_role is not None:
                    msg += await self.removeroleifpresent(member, member_role)

            if player_in_club and player.club.tag in tags:
                for role in ch.guild.roles:
                    if sub(r'[^\x00-\x7f]', r'', role.name).strip() == sub(
                            r'[^\x00-\x7f]', r'', player.club.name).strip():
                        member_role_expected = role
                        break
                if member_role_expected is None:
                    msg += await self.removeroleifpresent(member, guest, newcomer, vp, pres, leadership, leadershipemb)
                    msg += await self.addroleifnotpresent(member, lafamily)
                    if msg != "":
                        await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg, title=str(member)))
                    continue
                msg += await self.removeroleifpresent(member, guest, newcomer)
                msg += await self.addroleifnotpresent(member, lafamily)
                if member_role is None:
                    msg += await self.addroleifnotpresent(member, member_role_expected)
                elif member_role != member_role_expected:
                    msg += await self.removeroleifpresent(member, member_role)
                    msg += await self.addroleifnotpresent(member, member_role_expected)
                try:
                    await asyncio.sleep(0.5)
                    player_club = await self.ofcbsapi.get_club(player.club.tag)
                    for mem in player_club.members:
                        if mem.tag == player.raw_data['tag']:
                            if mem.role.lower() == 'vicepresident':
                                msg += await self.addroleifnotpresent(member, vp, leadership, leadershipemb)
                                msg += await self.removeroleifpresent(member, pres)
                            elif mem.role.lower() == 'president':
                                msg += await self.addroleifnotpresent(member, pres, leadership, leadershipemb)
                                msg += await self.removeroleifpresent(member, vp)
                            elif mem.role.lower() == 'member':
                                msg += await self.removeroleifpresent(member, vp, pres, leadership, leadershipemb)
                            break
                except brawlstats.errors.RequestError:
                    pass
            if msg != "":
                await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg, title=str(member)))

    @sortrolesasia.before_loop
    async def before_sortrolesasia(self):
        await asyncio.sleep(5)

    @tasks.loop(hours=6)
    async def sortrolesbd(self):
        ch = self.bot.get_channel(690881058756886599)
        await ch.trigger_typing()
        bs = ch.guild.get_role(678062773938159627)
        lamember = ch.guild.get_role(678062771069517825)
        newcomer = ch.guild.get_role(678623072143540225)
        guest = ch.guild.get_role(678062759711211546)
        pres = ch.guild.get_role(678062737338793984)
        vp = ch.guild.get_role(678062737963614211)
        leadership = ch.guild.get_role(690872028474900550)
        zerotwo = ch.guild.get_role(691297688297406596)
        twofour = ch.guild.get_role(678062784834961436)
        foursix = ch.guild.get_role(678062785049133129)
        sixeight = ch.guild.get_role(678062785917354035)
        eightten = ch.guild.get_role(678062786508750859)
        tenthirteen = ch.guild.get_role(678062788480073739)
        thirteensixteen = ch.guild.get_role(678062787267788801)
        sixteentwenty = ch.guild.get_role(678062787867443211)
        twenty = ch.guild.get_role(691297775626879007)
        error_counter = 0

        for member in ch.guild.members:
            if member.bot:
                continue
            tag = await self.config.user(member).tag()
            if tag is None:
                continue
            try:
                player = await self.ofcbsapi.get_player(tag)
                await asyncio.sleep(0.2)
            except brawlstats.errors.RequestError as e:
                error_counter += 1
                if error_counter == 5:
                    await ch.send(embed=discord.Embed(colour=discord.Colour.red(),
                                                      description=f"Stopping after 5 request errors! Displaying the last one:\n({str(e)})"))
                    break
                await asyncio.sleep(1)
                continue
            except Exception as e:
                return await ch.send(embed=discord.Embed(colour=discord.Colour.red(),
                                                         description=f"**Something went wrong while requesting {tag}!**\n({str(e)})"))

            msg = ""
            player_in_club = "name" in player.raw_data["club"]
            member_roles = []
            member_role = None
            member_role_expected = None

            if player.trophies < 2000:
                msg += await self.addroleifnotpresent(member, zerotwo)
                msg += await self.removeroleifpresent(member, twofour, foursix, sixeight, eightten, tenthirteen, thirteensixteen, sixteentwenty, twenty)
            elif 2000 <= player.trophies < 4000:
                msg += await self.addroleifnotpresent(member, twofour)
                msg += await self.removeroleifpresent(member, zerotwo, foursix, sixeight, eightten, tenthirteen,
                                                      thirteensixteen, sixteentwenty, twenty)
            elif 4000 <= player.trophies < 6000:
                msg += await self.addroleifnotpresent(member, foursix)
                msg += await self.removeroleifpresent(member, twofour, zerotwo, sixeight, eightten, tenthirteen,
                                                      thirteensixteen, sixteentwenty, twenty)
            elif 6000 <= player.trophies < 8000:
                msg += await self.addroleifnotpresent(member, sixeight)
                msg += await self.removeroleifpresent(member, twofour, foursix, zerotwo, eightten, tenthirteen,
                                                      thirteensixteen, sixteentwenty, twenty)
            elif 8000 <= player.trophies < 10000:
                msg += await self.addroleifnotpresent(member, eightten)
                msg += await self.removeroleifpresent(member, twofour, foursix, sixeight, zerotwo, tenthirteen,
                                                      thirteensixteen, sixteentwenty, twenty)
            elif 10000 <= player.trophies < 13000:
                msg += await self.addroleifnotpresent(member, tenthirteen)
                msg += await self.removeroleifpresent(member, twofour, foursix, sixeight, eightten, zerotwo,
                                                      thirteensixteen, sixteentwenty, twenty)
            elif 13000 <= player.trophies < 16000:
                msg += await self.addroleifnotpresent(member, thirteensixteen)
                msg += await self.removeroleifpresent(member, twofour, foursix, sixeight, eightten, tenthirteen,
                                                      zerotwo, sixteentwenty, twenty)
            elif 16000 <= player.trophies < 20000:
                msg += await self.addroleifnotpresent(member, sixteentwenty)
                msg += await self.removeroleifpresent(member, twofour, foursix, sixeight, eightten, tenthirteen,
                                                      thirteensixteen, zerotwo, twenty)
            elif 20000 <= player.trophies:
                msg += await self.addroleifnotpresent(member, twenty)
                msg += await self.removeroleifpresent(member, twofour, foursix, sixeight, eightten, tenthirteen,
                                                      thirteensixteen, sixteentwenty, zerotwo)

            for role in member.roles:
                if role.name.startswith('LA '):
                    member_roles.append(role)

            if len(member_roles) > 1:
                msg += f"Found more than one club role. (**{', '.join([str(r) for r in member_roles])}**)\n"
                for role in member_roles:
                    if sub(r'[^\x00-\x7f]', r'', role.name).strip() != sub(r'[^\x00-\x7f]', r'',
                                                                           player.club.name).strip():
                        msg += await self.removeroleifpresent(member, role)

            member_role = None if len(member_roles) < 1 else member_roles[0]

            if not player_in_club:
                msg += await self.removeroleifpresent(member, lamember, vp, pres, leadership, newcomer)
                msg += await self.addroleifnotpresent(member, guest)
                if member_role is not None:
                    msg += await self.removeroleifpresent(member, member_role)

            if player_in_club and not player.club.name.startswith("LA "):
                msg += await self.removeroleifpresent(member, lamember, vp, pres, leadership, newcomer)
                msg += await self.addroleifnotpresent(member, guest, bs)
                if member_role is not None:
                    msg += await self.removeroleifpresent(member, member_role)

            if player_in_club and player.club.name.startswith("LA "):
                for role in ch.guild.roles:
                    if sub(r'[^\x00-\x7f]', r'', role.name).strip() == sub(r'[^\x00-\x7f]', r'',
                                                                           player.club.name).strip():
                        member_role_expected = role
                        break
                msg += await self.removeroleifpresent(member, guest, newcomer)
                msg += await self.addroleifnotpresent(member, lamember, bs)
                if member_role is None:
                    msg += await self.addroleifnotpresent(member, member_role_expected)
                elif member_role != member_role_expected:
                    msg += await self.removeroleifpresent(member, member_role)
                    msg += await self.addroleifnotpresent(member, member_role_expected)
                if member_role_expected is not None:
                    try:
                        await asyncio.sleep(0.2)
                        player_club = await self.ofcbsapi.get_club(player.club.tag)
                        for mem in player_club.members:
                            if mem.tag == player.raw_data['tag']:
                                if mem.role.lower() == 'vicepresident':
                                    msg += await self.addroleifnotpresent(member, vp, leadership)
                                    msg += await self.removeroleifpresent(member, pres)
                                elif mem.role.lower() == 'president':
                                    msg += await self.addroleifnotpresent(member, pres, leadership)
                                    msg += await self.removeroleifpresent(member, vp)
                                elif mem.role.lower() == 'member':
                                    msg += await self.removeroleifpresent(member, vp, pres, leadership)
                                break
                    except brawlstats.errors.RequestError:
                        pass
                elif member_role_expected is None:
                    msg += await self.removeroleifpresent(member, vp, pres, leadership)
            if msg != "":
                await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg, title=str(member),
                                                  timestamp=datetime.datetime.now()))

    @sortrolesbd.before_loop
    async def before_sortrolesbd(self):
        await asyncio.sleep(5)

    @tasks.loop(hours=6)
    async def sortrolesspain(self):
        ch = self.bot.get_channel(693781513363390475)
        await ch.trigger_typing()
        memberrole = ch.guild.get_role(526805067165073408)
        guest = ch.guild.get_role(574176894627479583)
        newcomer = ch.guild.get_role(569473123942924308)
        otherclubs = ch.guild.get_role(601518751472549918)
        error_counter = 0

        for member in ch.guild.members:
            if member.bot:
                continue
            tag = await self.config.user(member).tag()
            if tag is None:
                continue
            try:
                player = await self.ofcbsapi.get_player(tag)
                await asyncio.sleep(0.5)
            except brawlstats.errors.RequestError as e:
                error_counter += 1
                if error_counter == 20:
                    await ch.send(embed=discord.Embed(colour=discord.Colour.red(),
                                                      description=f"¡Deteniéndose después de 5 errores de solicitud! Mostrando el último: \n({str(e)})"))
                    break
                await asyncio.sleep(1)
                continue
            except Exception as e:
                return await ch.send(embed=discord.Embed(colour=discord.Colour.red(),
                                                         description=f"**Algo ha ido mal solicitando {tag}!**\n({str(e)})"))

            msg = ""
            player_in_club = "name" in player.raw_data["club"]
            member_roles = []
            member_role = None
            member_role_expected = None
            tags = []
            guilds = await self.config.all_guilds()
            spain = guilds[460550486257565697]
            clubs = spain["clubs"]
            for club in clubs:
                info = clubs[club]
                tagn = "#" + info["tag"]
                tags.append(tagn)

            for role in member.roles:
                if role.name.startswith('LA '):
                    member_roles.append(role)

            if len(member_roles) > 1:
                msg += f"Se ha encontrado más de un rol de club. **{', '.join([str(r) for r in member_roles])}**"
                member_role = member_roles[0]
                for role in member_roles[1:]:
                    msg += await self.removeroleifpresent(member, role)

            member_role = None if len(member_roles) < 1 else member_roles[0]

            if not player_in_club:
                msg += await self.removeroleifpresent(member, memberrole, otherclubs, newcomer)
                msg += await self.addroleifnotpresent(member, guest)
                if member_role is not None:
                    msg += await self.removeroleifpresent(member, member_role)

            if player_in_club and "LA " not in player.club.name and player.club.tag not in tags:
                msg += await self.removeroleifpresent(member, memberrole, otherclubs, newcomer)
                msg += await self.addroleifnotpresent(member, guest)
                if member_role is not None:
                    msg += await self.removeroleifpresent(member, member_role)

            if player_in_club and "LA " in player.club.name and player.club.tag not in tags:
                msg += await self.removeroleifpresent(member,  newcomer)
                msg += await self.addroleifnotpresent(member, memberrole, otherclubs)
                if member_role is not None:
                    msg += await self.removeroleifpresent(member, member_role)

            if player_in_club and player.club.tag in tags:
                for role in ch.guild.roles:
                    if sub(r'[^\x00-\x7f]', r'', role.name).strip() == sub(
                            r'[^\x00-\x7f]', r'', player.club.name).strip():
                        member_role_expected = role
                        break
                msg += await self.removeroleifpresent(member, guest, newcomer)
                msg += await self.addroleifnotpresent(member, memberrole)
                if member_role is None:
                    msg += await self.addroleifnotpresent(member, member_role_expected)
                elif member_role != member_role_expected:
                    msg += await self.removeroleifpresent(member, member_role)
                    msg += await self.addroleifnotpresent(member, member_role_expected)
            if msg != "":
                await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg, title=str(member)))


    @sortrolesspain.before_loop
    async def before_sortrolesspain(self):
        await asyncio.sleep(5)

    @commands.command()
    @commands.guild_only()
    async def newcomer(self, ctx, tag, member: discord.Member):
        """Command to set up a new member"""
        if ctx.guild.id == 401883208511389716:
            mod = ctx.guild.get_role(520719415109746690)
            tmod = ctx.guild.get_role(533650638274297877)
            roles = ctx.guild.get_role(564552111875162112)

            if mod not in ctx.author.roles and roles not in ctx.author.roles and tmod not in ctx.author.roles and not ctx.author.guild_permissions.administrator and ctx.author.id != 359131399132807178:
                return await ctx.send("You can't use this command.")

            await ctx.trigger_typing()

            labs = ctx.guild.get_role(576028728052809728)
            guest = ctx.guild.get_role(578260960981286923)
            newcomer = ctx.guild.get_role(534461445656543255)
            brawlstars = ctx.guild.get_role(576002604740378629)
            vp = ctx.guild.get_role(536993652648574976)
            pres = ctx.guild.get_role(536993632918568991)

            tag = tag.lower().replace('O', '0')
            if tag.startswith("#"):
                tag = tag.strip('#')

            msg = ""
            try:
                player = await self.ofcbsapi.get_player(tag)
                await self.config.user(member).tag.set(tag.replace("#", ""))
                msg += f"BS account **{player.name}** was saved to **{member.name}**\n"
            except brawlstats.errors.NotFoundError:
                return await ctx.send(embed=badEmbed("No player with this tag found!"))

            except brawlstats.errors.RequestError as e:
                return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

            except Exception as e:
                return await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!****")

            nick = f"{player.name}"
            try:
                await member.edit(nick=nick[:31])
                msg += f"New nickname: **{nick[:31]}**\n"
            except discord.Forbidden:
                msg += f"I dont have permission to change nickname of this user!\n"
            except Exception as e:
                return await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=f"Something went wrong: {str(e)}"))

            player_in_club = "name" in player.raw_data["club"]
            member_role_expected = None

            if not player_in_club:
                msg += await self.removeroleifpresent(member, newcomer)
                msg += await self.addroleifnotpresent(member, guest, brawlstars)

            if player_in_club and "LA " not in player.club.name:
                msg += await self.removeroleifpresent(member, newcomer)
                msg += await self.addroleifnotpresent(member, guest, brawlstars)

            if player_in_club and "LA " in player.club.name:
                for role in ctx.guild.roles:
                    if sub(r'[^\x00-\x7f]', r'', role.name).strip() == sub(
                            r'[^\x00-\x7f]', r'', player.club.name).strip():
                        member_role_expected = role
                        break
                if member_role_expected is None:
                    msg += await self.removeroleifpresent(member, newcomer)
                    msg += await self.addroleifnotpresent(member, guest, brawlstars)
                    msg += f"Role for the club {player.club.name} not found.\n"
                    return await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))
                msg += await self.removeroleifpresent(member, newcomer)
                msg += await self.addroleifnotpresent(member, labs, brawlstars)
                msg += await self.addroleifnotpresent(member, member_role_expected)
                try:
                    player_club = await self.ofcbsapi.get_club(player.club.tag)
                    for mem in player_club.members:
                        if mem.tag == player.raw_data['tag']:
                            if mem.role.lower() == 'vicepresident':
                                msg += await self.addroleifnotpresent(member, vp)
                            elif mem.role.lower() == 'president':
                                msg += await self.addroleifnotpresent(member, pres)
                            break
                except brawlstats.errors.RequestError:
                    msg += "<:offline:642094554019004416> Couldn't retrieve player's club role."
            if msg != "":
                await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))

        elif ctx.guild.id == 663716223258984496:
            mod = ctx.guild.get_role(663792825493618709)
            staff = ctx.guild.get_role(663792418751250432)

            if mod not in ctx.author.roles and staff not in ctx.author.roles and not ctx.author.guild_permissions.administrator  and ctx.author.id != 359131399132807178:
                return await ctx.send("You can't use this command.")

            await ctx.trigger_typing()

            lafamily = ctx.guild.get_role(663795352666636305)
            guest = ctx.guild.get_role(663798304194166854)
            newcomer = ctx.guild.get_role(663799853889093652)
            vp = ctx.guild.get_role(663793699972579329)
            pres = ctx.guild.get_role(663793444199596032)
            leadership = ctx.guild.get_role(663910848569409598)

            tags = []
            guilds = await self.config.all_guilds()
            asia = guilds[663716223258984496]
            clubs = asia["clubs"]
            for club in clubs:
                info = clubs[club]
                tagn = "#" + info["tag"]
                tags.append(tagn)

            tag = tag.lower().replace('O', '0')
            if tag.startswith("#"):
                tag = tag.strip('#')

            msg = ""
            try:
                player = await self.ofcbsapi.get_player(tag)
                await self.config.user(member).tag.set(tag.replace("#", ""))
                msg += f"BS account **{player.name}** was saved to **{member.name}**\n"

            except brawlstats.errors.NotFoundError:
                return await ctx.send(embed=badEmbed("No player with this tag found!"))

            except brawlstats.errors.RequestError as e:
                return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

            except Exception as e:
                return await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!****")

            nick = f"{player.name}"
            try:
                await member.edit(nick=nick[:31])
                msg += f"New nickname: **{nick[:31]}**\n"
            except discord.Forbidden:
                msg += f"I dont have permission to change nickname of this user!\n"
            except Exception as e:
                return await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=f"Something went wrong: {str(e)}"))

            player_in_club = "name" in player.raw_data["club"]
            member_role_expected = None

            if not player_in_club:
                msg += await self.removeroleifpresent(member, newcomer)
                msg += await self.addroleifnotpresent(member, guest)

            if player_in_club and player.club.tag not in tags:
                msg += await self.removeroleifpresent(member, newcomer)
                msg += await self.addroleifnotpresent(member, guest)

            if player_in_club and player.club.tag in tags:
                for role in ctx.guild.roles:
                    if sub(r'[^\x00-\x7f]', r'', role.name).strip() == sub(
                            r'[^\x00-\x7f]', r'', player.club.name).strip():
                        member_role_expected = role
                        break
                if member_role_expected is None:
                    msg += await self.removeroleifpresent(member, newcomer)
                    msg += await self.addroleifnotpresent(member, lafamily)
                    return await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))
                msg += await self.removeroleifpresent(member, newcomer)
                msg += await self.addroleifnotpresent(member, lafamily, member_role_expected)
                try:
                    player_club = await self.ofcbsapi.get_club(player.club.tag)
                    for mem in player_club.members:
                        if mem.tag == player.raw_data['tag']:
                            if mem.role.lower() == 'vicepresident':
                                msg += await self.addroleifnotpresent(member, vp, leadership)
                            elif mem.role.lower() == 'president':
                                msg += await self.addroleifnotpresent(member, pres, leadership)
                            break
                except brawlstats.errors.RequestError:
                    msg += "<:offline:642094554019004416> Couldn't retrieve player's club role."
            if msg != "":
                await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))

        elif ctx.guild.id == 593732431551660063:
            staff = ctx.guild.get_role(678623063344021504)
            hub = ctx.guild.get_role(678062772679868459)

            if staff not in ctx.author.roles and hub not in ctx.author.roles and not ctx.author.guild_permissions.administrator  and ctx.author.id != 359131399132807178:
                return await ctx.send("You can't use this command.")

            await ctx.trigger_typing()

            bs = ctx.guild.get_role(678062773938159627)
            lamember = ctx.guild.get_role(678062771069517825)
            newcomer = ctx.guild.get_role(678623072143540225)
            guest = ctx.guild.get_role(678062759711211546)
            pres = ctx.guild.get_role(678062737338793984)
            vp = ctx.guild.get_role(678062737963614211)
            leadership = ctx.guild.get_role(690872028474900550)
            zerotwo = ctx.guild.get_role(691297688297406596)
            twofour = ctx.guild.get_role(678062784834961436)
            foursix = ctx.guild.get_role(678062785049133129)
            sixeight = ctx.guild.get_role(678062785917354035)
            eightten = ctx.guild.get_role(678062786508750859)
            tenthirteen = ctx.guild.get_role(678062788480073739)
            thirteensixteen = ctx.guild.get_role(678062787267788801)
            sixteentwenty = ctx.guild.get_role(678062787867443211)
            twenty = ctx.guild.get_role(691297775626879007)
            ootw = ctx.guild.get_role(678062761154183168)
            ptw = ctx.guild.get_role(678062765381779496)
            pt = ctx.guild.get_role(678062764673073152)
            pbc = ctx.guild.get_role(678062765729906720)
            alls = ctx.guild.get_role(678062763267850280)

            tag = tag.lower().replace('O', '0')
            if tag.startswith("#"):
                tag = tag.strip('#')

            msg = ""
            try:
                player = await self.ofcbsapi.get_player(tag)
                await self.config.user(member).tag.set(tag.replace("#", ""))
                msg += f"BS account **{player.name}** was saved to **{member.name}**\n"

            except brawlstats.errors.NotFoundError:
                return await ctx.send(embed=badEmbed("No player with this tag found!"))

            except brawlstats.errors.RequestError as e:
                return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

            except Exception as e:
                return await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!****")

            nick = f"{player.name}"
            try:
                await member.edit(nick=nick[:31])
                msg += f"New nickname: **{nick[:31]}**\n"
            except discord.Forbidden:
                msg += f"I dont have permission to change nickname of this user!\n"
            except Exception as e:
                return await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=f"Something went wrong: {str(e)}"))

            player_in_club = "name" in player.raw_data["club"]
            member_role_expected = None

            if player.trophies < 2000:
                msg += await self.addroleifnotpresent(member, zerotwo)
            elif 2000 <= player.trophies < 4000:
                msg += await self.addroleifnotpresent(member, twofour)
            elif 4000 <= player.trophies < 6000:
                msg += await self.addroleifnotpresent(member, foursix)
            elif 6000 <= player.trophies < 8000:
                msg += await self.addroleifnotpresent(member, sixeight)
            elif 8000 <= player.trophies < 10000:
                msg += await self.addroleifnotpresent(member, eightten)
            elif 10000 <= player.trophies < 13000:
                msg += await self.addroleifnotpresent(member, tenthirteen)
            elif 13000 <= player.trophies < 16000:
                msg += await self.addroleifnotpresent(member, thirteensixteen)
            elif 16000 <= player.trophies < 20000:
                msg += await self.addroleifnotpresent(member, sixteentwenty)
            elif 20000 <= player.trophies:
                msg += await self.addroleifnotpresent(member, twenty)

            if player.trophies > 14500:
                msg += await self.addroleifnotpresent(member, ootw)

            if player.raw_data['3vs3Victories'] >= 10000:
                msg += await self.addroleifnotpresent(member, ptw)

            if player.solo_victories >= 3000:
                msg += await self.addroleifnotpresent(member, pt)

            if player.duo_victories >= 1500:
                msg += await self.addroleifnotpresent(member, pbc)

            valid = True
            if len(player.raw_data['brawlers']) != 34:
                valid = False
            for brawler in player.raw_data['brawlers']:
                if len(brawler.get('starPowers')) != 2:
                    valid = False
            if valid:
                msg += await self.addroleifnotpresent(member, alls)

            if not player_in_club:
                msg += await self.removeroleifpresent(member, newcomer)
                msg += await self.addroleifnotpresent(member, guest, bs)

            if player_in_club and "LA " not in player.club.name:
                msg += await self.removeroleifpresent(member, newcomer)
                msg += await self.addroleifnotpresent(member, guest, bs)

            if player_in_club and "LA " in player.club.name:
                for role in ctx.guild.roles:
                    if sub(r'[^\x00-\x7f]', r'', role.name).strip() == sub(
                            r'[^\x00-\x7f]', r'', player.club.name).strip():
                        member_role_expected = role
                        break
                if member_role_expected is None:
                    msg += await self.removeroleifpresent(member, newcomer)
                    msg += await self.addroleifnotpresent(member, lamember, bs)
                    return await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))
                msg += await self.removeroleifpresent(member, newcomer)
                msg += await self.addroleifnotpresent(member, lamember, bs)
                msg += await self.addroleifnotpresent(member, member_role_expected)
                try:
                    player_club = await self.ofcbsapi.get_club(player.club.tag)
                    for mem in player_club.members:
                        if mem.tag == player.raw_data['tag']:
                            if mem.role.lower() == 'vicepresident':
                                msg += await self.addroleifnotpresent(member, vp, leadership)
                            elif mem.role.lower() == 'president':
                                msg += await self.addroleifnotpresent(member, pres, leadership)
                            break
                except brawlstats.errors.RequestError:
                    msg += "<:offline:642094554019004416> Couldn't retrieve player's club role."

            if msg != "":
                await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))

    @commands.command()
    @commands.guild_only()
    async def vincular(self, ctx, tag, member: discord.Member = None):
        """LA Spain's verification command"""
        if ctx.channel.id != 590962715795783684:
            return await ctx.send(embed=discord.Embed(colour=discord.Colour.red(), description="No puedes usar este comando en este servidor."))

        await ctx.trigger_typing()

        memberrole = ctx.guild.get_role(526805067165073408)
        guest = ctx.guild.get_role(574176894627479583)
        newcomer = ctx.guild.get_role(569473123942924308)
        otherclubs = ctx.guild.get_role(601518751472549918)

        if member is not None:
            if newcomer in ctx.author.roles:
                return
        elif member is None:
            member = ctx.author

        if newcomer not in member.roles:
            return await ctx.send("No eres nuevo, no puedes usar ese comando.")

        tag = tag.lower().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        tags = []
        guilds = await self.config.all_guilds()
        spain = guilds[460550486257565697]
        clubs = spain["clubs"]
        for club in clubs:
            info = clubs[club]
            tagn = "#" + info["tag"]
            tags.append(tagn)

        msg = ""
        try:
            player = await self.ofcbsapi.get_player(tag)
            await self.config.user(member).tag.set(tag.replace("#", ""))
            msg += f"Cuenta de BS **{player.name}** guardada para **{member.name}**\n"
        except brawlstats.errors.NotFoundError:
            return await ctx.send(embed=badEmbed("¡No se ha encontrado ningún jugador con este tag!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send(
                "**¡Algo ha ido mal, por favor envía un mensaje personal al bot LA Modmail o inténtalo de nuevo!**")

        nick = f"{player.name}"
        try:
            await member.edit(nick=nick[:31])
            msg += f"Nuevo apodo: **{nick[:31]}**\n"
        except discord.Forbidden:
            msg += f"¡No tengo permisos para cambiar el apodo de este usuario!\n"
        except Exception as e:
            return await ctx.send(
                embed=discord.Embed(colour=discord.Colour.blue(), description=f"¡Algo ha ido mal: {str(e)}"))

        player_in_club = "name" in player.raw_data["club"]
        member_role_expected = None

        if not player_in_club:
            msg += await self.removeroleifpresent(member, newcomer)
            msg += await self.addroleifnotpresent(member, guest)

        if player_in_club and not player.club.name.startswith("LA") and player.club.tag not in tags:
            msg += await self.removeroleifpresent(member, newcomer)
            msg += await self.addroleifnotpresent(member, guest)

        if player_in_club and player.club.name.startswith("LA") and player.club.tag not in tags:
            msg += await self.removeroleifpresent(member, newcomer)
            msg += await self.addroleifnotpresent(member, memberrole, otherclubs)

        if player_in_club and player.club.tag in tags:
            for role in ctx.guild.roles:
                if sub(r'[^\x00-\x7f]', r'', role.name).strip() == sub(
                        r'[^\x00-\x7f]', r'', player.club.name).strip():
                    member_role_expected = role
                    break
            if member_role_expected is None:
                return await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(),
                                                          description=f"No se ha encontrado un rol para el club {player.club.name}. Input: {club_name}.\n"))
            msg += await self.removeroleifpresent(member, newcomer)
            msg += await self.addroleifnotpresent(member, memberrole)
            msg += await self.addroleifnotpresent(member, member_role_expected)
        if msg != "":
            await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))

    @commands.command()
    @commands.guild_only()
    async def nuevorol(self, ctx, tag, member: discord.Member):
        """Verification command for LA DeRucula"""
        staff = ctx.guild.get_role(632418886217760789)
        lider = ctx.guild.get_role(632447350820044811)
        admin = ctx.guild.get_role(632419834939965450)

        if staff not in ctx.author.roles and lider not in ctx.author.roles and admin not in ctx.author.roles and not ctx.author.guild_permissions.administrator and ctx.author.id != 359131399132807178:
            return await ctx.send("You can't use this command.")

        await ctx.trigger_typing()

        derucula = ctx.guild.get_role(632420307872907295)
        cl = ctx.guild.get_role(700896108745982023)
        co = ctx.guild.get_role(700895961551077387)
        uy = ctx.guild.get_role(700896097987723374)
        ve = ctx.guild.get_role(700895968652034133)
        hn = ctx.guild.get_role(705409643375231036)
        mx = ctx.guild.get_role(700896011375214623)
        otros = ctx.guild.get_role(700896019134808116)
        pres = ctx.guild.get_roles(703699073697579019)
        vp = ctx.guild.get_roles(703698676014383154)

        tags = []
        guilds = await self.config.all_guilds()
        latam = guilds[631888808224489482]
        clubs = latam["clubs"]
        for club in clubs:
            info = clubs[club]
            tagn = "#" + info["tag"]
            tags.append(tagn)

        tag = tag.lower().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        msg = ""
        try:
            player = await self.ofcbsapi.get_player(tag)
            await self.config.user(member).tag.set(tag.replace("#", ""))
            msg += f"BS account **{player.name}** was saved to **{member.name}**\n"
        except brawlstats.errors.NotFoundError:
            return await ctx.send(embed=badEmbed("No player with this tag found!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send(
                "**Something went wrong, please send a personal message to LA Modmail bot or try again!****")

        nick = f"{player.name}"
        try:
            await member.edit(nick=nick[:31])
            msg += f"New nickname: **{nick[:31]}**\n"
        except discord.Forbidden:
            msg += f"I dont have permission to change nickname of this user!\n"
        except Exception as e:
            return await ctx.send(
                embed=discord.Embed(colour=discord.Colour.blue(), description=f"Something went wrong: {str(e)}"))

        player_in_club = "name" in player.raw_data["club"]

        if player_in_club and "LA " in player.club.name and player.club.tag not in tags:
            msg += await self.addroleifnotpresent(member, otros)

        if player_in_club and player.club.tag in tags:
            msg += await self.addroleifnotpresent(member, derucula)
            if " CL" in player.club.name:
                msg += await self.addroleifnotpresent(member, cl)
            elif " CO" in player.club.name:
                msg += await self.addroleifnotpresent(member, co)
            elif " UY" in player.club.name:
                msg += await self.addroleifnotpresent(member, uy)
            elif " VE" in player.club.name:
                msg += await self.addroleifnotpresent(member, ve)
            elif " HN" in player.club.name:
                msg += await self.addroleifnotpresent(member, hn)
            elif " MX" in player.club.name:
                msg += await self.addroleifnotpresent(member, mx)
            try:
                player_club = await self.ofcbsapi.get_club(player.club.tag)
                for mem in player_club.members:
                    if mem.tag == player.raw_data['tag']:
                        if mem.role.lower() == 'vicepresident':
                            msg += await self.addroleifnotpresent(member, vp)
                        elif mem.role.lower() == 'president':
                            msg += await self.addroleifnotpresent(member, pres)
                        break
            except brawlstats.errors.RequestError:
                msg += "<:offline:642094554019004416> Couldn't retrieve player's club role."

        if msg != "":
            await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))

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

    @commands.command()
    @commands.guild_only()
    async def lowclubs(self, ctx):
        """Show all the clubs in your server that are low on members"""
        offline = False
        await ctx.trigger_typing()

        if len((await self.config.guild(ctx.guild).clubs()).keys()) < 1:
            return await ctx.send(
                embed=badEmbed(f"This server has no clubs saved. Save a club by using {ctx.prefix}clubs add!"))

        try:
            try:
                clubs = []
                for key in (await self.config.guild(ctx.guild).clubs()).keys():
                    club = await self.ofcbsapi.get_club(await self.config.guild(ctx.guild).clubs.get_raw(key, "tag"))
                    clubs.append(club)
            except brawlstats.errors.RequestError as e:
                offline = True

            embedFields = []

            if not offline:
                clubs = sorted(clubs, key=lambda sort: (
                    sort.trophies), reverse=True)

                for i in range(len(clubs)):
                    if len(clubs[i].members) <= 92:
                        key = ""
                        for k in (await self.config.guild(ctx.guild).clubs()).keys():
                            if clubs[i].tag.replace("#", "") == await self.config.guild(ctx.guild).clubs.get_raw(k, "tag"):
                                key = k

                        await self.config.guild(ctx.guild).clubs.set_raw(key, 'lastMemberCount',
                                                                         value=len(clubs[i].members))
                        await self.config.guild(ctx.guild).clubs.set_raw(key, 'lastRequirement',
                                                                         value=clubs[i].required_trophies)
                        await self.config.guild(ctx.guild).clubs.set_raw(key, 'lastScore', value=clubs[i].trophies)
                        await self.config.guild(ctx.guild).clubs.set_raw(key, 'lastPosition', value=i)

                        info = await self.config.guild(ctx.guild).clubs.get_raw(key, "info", default="")
                        e_name = f"<:bsband:600741378497970177> {clubs[i].name} [{key}] {clubs[i].tag} {info}"
                        e_value = f"<:bstrophy:552558722770141204>`{clubs[i].trophies}` {get_league_emoji(clubs[i].required_trophies)}`{clubs[i].required_trophies}+` <:icon_gameroom:553299647729238016>`{len(clubs[i].members)}`"
                        embedFields.append([e_name, e_value])

            else:
                if len(clubs[i].members) <= 92:
                    offclubs = []
                    for k in (await self.config.guild(ctx.guild).clubs()).keys():
                        offclubs.append([await self.config.guild(ctx.guild).clubs.get_raw(k, "lastPosition"), k])
                    offclubs = sorted(offclubs, key=lambda x: x[0])

                    for club in offclubs:
                        ckey = club[1]
                        cscore = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "lastScore")
                        cname = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "name")
                        ctag = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "tag")
                        cinfo = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "info")
                        cmembers = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "lastMemberCount")
                        creq = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "lastRequirement")

                        e_name = f"<:bsband:600741378497970177> {cname} [{ckey}] #{ctag} {cinfo}"
                        e_value = f"<:bstrophy:552558722770141204>`{cscore}` {get_league_emoji(creq)}`{creq}+` <:icon_gameroom:553299647729238016>`{cmembers}` "
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
                footer = "<:offline:642094554019004416> API is offline, showing last saved data." if offline else f"Need more info about a club? Use {ctx.prefix}club [key]"
                embed.set_footer(text=footer)
                for e in embedFields[i:i + 8]:
                    embed.add_field(name=e[0], value=e[1], inline=False)
                embedsToSend.append(embed)

            if len(embedsToSend) > 1:
                await menu(ctx, embedsToSend, {"⬅": prev_page, "➡": next_page, }, timeout=2000)
            else:
                await ctx.send(embed=embedsToSend[0])

        except ZeroDivisionError as e:
            return await ctx.send(
                "**Something went wrong, please send a personal message to LA Modmail bot or try again!**")

    @commands.command()
    @commands.guild_only()
    async def whitelistclubs(self, ctx):
        """Utility command for whitelist in LA Gaming - Brawl Stars"""
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
            if tag is None:
                msg += f"**{member.name}**: has no tag saved.\n"
            try:
                player = await self.ofcbsapi.get_player(tag)
                await asyncio.sleep(0.2)
            except brawlstats.errors.RequestError as e:
                msg += f"**{member.name}**: request error.\n"
                continue
            except Exception as e:
                msg += "Something went wrong."
                return
            player_in_club = "name" in player.raw_data["club"]
            if len(msg) > 1900:
                messages.append(msg)
                msg = ""
            if player_in_club:
                clubobj = await self.ofcbsapi.get_club(player.club.tag)
                msg += f"**{str(member)}** `{player.trophies}` <:bstrophy:552558722770141204>: {player.club.name} ({len(clubobj.members)}/100)\n"
            else:
                msg += f"**{str(member)}** `{player.trophies}` <:bstrophy:552558722770141204>: not in a club.\n"
        if len(msg) > 0:
            messages.append(msg)
        for m in messages:
            await ctx.send(embed=discord.Embed(colour=discord.Colour.green(), description=m))