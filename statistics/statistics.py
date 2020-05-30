import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.menus import menu, prev_page, next_page
from bs.utils import badEmbed, goodEmbed
import asyncio
import brawlstats
import clashroyale
from discord.ext import tasks

class Statistics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=42424269)
        default_guild = {"blacklisted": {}}
        self.config.register_guild(**default_guild)
        self.bsconfig = Config.get_conf(None, identifier=5245652, cog_name="BrawlStarsCog")
        self.crconfig = Config.get_conf(None, identifier=2512325, cog_name="ClashRoyaleCog")
        self.lbrenewallabs.start()
        self.lbrenewalasia.start()
        self.lbrenewalbd.start()
        self.lbrenewalspain.start()

    def cog_unload(self):
        self.lbrenewallabs.cancel()
        self.lbrenewalasia.cancel()
        self.lbrenewalbd.cancel()
        self.lbrenewalspain.cancel()

    async def initialize(self):
        crapikey = await self.bot.get_shared_api_tokens("crapi")
        if crapikey["api_key"] is None:
            raise ValueError("The Clash Royale API key has not been set.")
        self.crapi = clashroyale.OfficialAPI(crapikey["api_key"], is_async=True)

        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.Client(ofcbsapikey["api_key"], is_async=True)

    @commands.is_owner()
    @commands.command()
    async def summary(self, ctx, key:str=None):
        if key is None:
            totaltrophies = 0
            averagetrophies = 0
            lower10 = 0
            members = []
            for key in (await self.bsconfig.guild(ctx.guild).clubs()).keys():
                tag = await self.bsconfig.guild(ctx.guild).clubs.get_raw(key, "tag")
                club = await self.ofcbsapi.get_club(tag)
                for member in club.members:
                    members.append(member.trophies)
            for mem in members:
                totaltrophies = totaltrophies + mem
            members.sort(reverse=True)
            for i in range(len(members) - (len(members)//10), len(members)):
                lower10 = lower10 + members[i]
            averagetrophies = totaltrophies//len(members)
            embed = discord.Embed(color=discord.Colour.gold(), title="All clubs:")
            embed.add_field(name="Total trophies:", value=totaltrophies, inline=False)
            embed.add_field(name="Total members:", value=len(members), inline=False)
            embed.add_field(name="Average trophies:", value=averagetrophies, inline=False)
            embed.add_field(name="Lower 10% average:", value=lower10//(len(members)//10), inline=False)
            await ctx.send(embed=embed)
        elif key is not None:
            lower10 = 0
            tag = await self.bsconfig.guild(ctx.guild).clubs.get_raw(key, "tag")
            club = await self.ofcbsapi.get_club(tag)
            for i in range(len(club.members) - (len(club.members)//10), len(club.members)):
                lower10 = lower10 + club.members[i].trophies
            embed = discord.Embed(color=discord.Colour.gold(), title=f"{club.name}:")
            embed.add_field(name="Total trophies:", value=club.trophies, inline=False)
            embed.add_field(name="Total members:", value=len(club.members), inline=False)
            embed.add_field(name="Average trophies:", value=club.trophies//len(club.members), inline=False)
            embed.add_field(name="Lower 10% average:", value=lower10 // (len(club.members)//10), inline=False)
            await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def trophylb(self, ctx, key:str=None):
        if key is None:
            trophies = []
            for key in (await self.bsconfig.guild(ctx.guild).clubs()).keys():
                tag = await self.bsconfig.guild(ctx.guild).clubs.get_raw(key, "tag")
                club = await self.ofcbsapi.get_club(tag)
                for member in club.members:
                    pair = []
                    pair.append(member.name)
                    pair.append(member.trophies)
                    pair.append(club.name)
                    trophies.append(pair)
            trophies = sorted(trophies, key=lambda x: x[1], reverse=True)
            msg = ""
            i = 1
            for trophy in trophies:
                if trophy == trophies[20]:
                    break
                msg += f"{i}. <:bstrophy:552558722770141204> {trophy[1]} **{trophy[0]}**({trophy[2]})\n"
                i = i + 1
            embed = discord.Embed(color=discord.Colour.gold(), title=f"{ctx.guild.name} leaderboard:", description=msg)
            await ctx.send(embed=embed)
        elif key is not None:
            tag = await self.bsconfig.guild(ctx.guild).clubs.get_raw(key, "tag")
            club = await self.ofcbsapi.get_club(tag)
            msg = ""
            i = 1
            for member in club.members:
                if member == club.members[20]:
                    break
                msg += f"{i}. <:bstrophy:552558722770141204> {member.trophies} **{member.name}**\n"
                i = i + 1
            embed = discord.Embed(color=discord.Colour.gold(), title=f"{club.name} leaderboard:", description=msg)
            await ctx.send(embed=embed)

    @tasks.loop(minutes=60)
    async def lbrenewallabs(self):
        channel = self.bot.get_channel(689889206230974473)
        if channel is not None:
            message = await channel.fetch_message(691747287814373428)
            message2 = await channel.fetch_message(691747288988647534)
            message3 = await channel.fetch_message(691747290398064741)
            message4 = await channel.fetch_message(691747291119222875)
            message5 = await channel.fetch_message(691747292511993866)
            trophies = []
            for key in (await self.bsconfig.guild(message.guild).clubs()).keys():
                tag = await self.bsconfig.guild(message.guild).clubs.get_raw(key, "tag")
                club = await self.ofcbsapi.get_club(tag)
                for member in club.members:
                    pair = []
                    pair.append(member.name)
                    pair.append(member.trophies)
                    pair.append(club.name)
                    trophies.append(pair)
            trophies = sorted(trophies, key=lambda x: x[1], reverse=True)
            messages = []
            msg = ""
            i = 1
            for trophy in trophies:
                if trophy == trophies[20] or trophy == trophies[40] or trophy == trophies[60] or trophy == trophies[80] or trophy == trophies[100]:
                    messages.append(msg)
                    msg = ""
                msg += f"{i}. <:bstrophy:552558722770141204> {trophy[1]} **{trophy[0]}**({trophy[2]})\n"
                i = i + 1
            for m in messages:
                if m == messages[0]:
                    embed = discord.Embed(color=discord.Colour.gold(), title=f"{message.guild.name} leaderboard:", description=m)
                    await message.edit(embed=embed)
                elif m == messages[1]:
                    embed = discord.Embed(color=discord.Colour.gold(), description=m)
                    await message2.edit(embed=embed)
                elif m == messages[2]:
                    embed = discord.Embed(color=discord.Colour.gold(), description=m)
                    await message3.edit(embed=embed)
                elif m == messages[3]:
                    embed = discord.Embed(color=discord.Colour.gold(), description=m)
                    await message4.edit(embed=embed)
                elif m == messages[4]:
                    embed = discord.Embed(color=discord.Colour.gold(), description=m)
                    await message5.edit(embed=embed)

    @tasks.loop(minutes=70)
    async def lbrenewalasia(self):
        channel = self.bot.get_channel(690133321245917204)
        if channel is not None:
            message = await channel.fetch_message(690133472366428160)
            trophies = []
            for key in (await self.bsconfig.guild(message.guild).clubs()).keys():
                tag = await self.bsconfig.guild(message.guild).clubs.get_raw(key, "tag")
                club = await self.ofcbsapi.get_club(tag)
                for member in club.members:
                    pair = []
                    pair.append(member.name)
                    pair.append(member.trophies)
                    pair.append(club.name)
                    trophies.append(pair)
            trophies = sorted(trophies, key=lambda x: x[1], reverse=True)
            msg = ""
            i = 1
            for trophy in trophies:
                if trophy == trophies[20]:
                    break
                msg += f"{i}. <:bstrophy:552558722770141204> {trophy[1]} **{trophy[0]}**({trophy[2]})\n"
                i = i + 1
            embed = discord.Embed(color=discord.Colour.gold(), title=f"{message.guild.name} leaderboard:", description=msg)
            await message.edit(embed=embed)

    @tasks.loop(minutes=80)
    async def lbrenewalbd(self):
        channel = self.bot.get_channel(691278145185251328)
        if channel is not None:
            message = await channel.fetch_message(691296279157801050)
            trophies = []
            for key in (await self.bsconfig.guild(message.guild).clubs()).keys():
                tag = await self.bsconfig.guild(message.guild).clubs.get_raw(key, "tag")
                club = await self.ofcbsapi.get_club(tag)
                for member in club.members:
                    pair = []
                    pair.append(member.name)
                    pair.append(member.trophies)
                    pair.append(club.name)
                    trophies.append(pair)
            trophies = sorted(trophies, key=lambda x: x[1], reverse=True)
            msg = ""
            i = 1
            for trophy in trophies:
                if trophy == trophies[20]:
                    break
                msg += f"{i}. <:bstrophy:552558722770141204> {trophy[1]} **{trophy[0]}**({trophy[2]})\n"
                i = i + 1
            embed = discord.Embed(color=discord.Colour.gold(), title=f"{message.guild.name} leaderboard:", description=msg)
            await message.edit(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def crtrophylb(self, ctx, key: str = None):
        if key is None:
            trophies = []
            for key in (await self.crconfig.guild(ctx.guild).clans()).keys():
                tag = await self.crconfig.guild(ctx.guild).clans.get_raw(key, "tag")
                clan = await self.crapi.get_clan(tag)
                for member in clan.memberList:
                    pair = []
                    pair.append(member.name)
                    pair.append(member.trophies)
                    pair.append(clan.name)
                    trophies.append(pair)
            trophies = sorted(trophies, key=lambda x: x[1], reverse=True)
            msg = ""
            i = 1
            for trophy in trophies:
                if trophy == trophies[20]:
                    break
                msg += f"{i}. <:trophycr:587316903001718789> {trophy[1]} **{trophy[0]}**({trophy[2]})\n"
                i = i + 1
            embed = discord.Embed(color=discord.Colour.gold(), title=f"{ctx.guild.name} leaderboard:", description=msg)
            await ctx.send(embed=embed)
        elif key is not None:
            tag = await self.crconfig.guild(ctx.guild).clans.get_raw(key, "tag")
            clan = await self.crapi.get_clan(tag)
            msg = ""
            i = 1
            for member in clan.memberList:
                if member == clan.memberList[20]:
                    break
                msg += f"{i}. <:trophycr:587316903001718789> {member.trophies} **{member.name}**\n"
                i = i + 1
            embed = discord.Embed(color=discord.Colour.gold(), title=f"{clan.name} leaderboard:", description=msg)
            await ctx.send(embed=embed)

    @tasks.loop(minutes=90)
    async def lbrenewalspain(self):
        channel = self.bot.get_channel(691413764867751986)
        if channel is not None:
            message = await channel.fetch_message(710984852798832690)
            message2 = await channel.fetch_message(710984856582225922)
            message3 = await channel.fetch_message(710984885854142484)
            message4 = await channel.fetch_message(710984892128821259)
            message5 = await channel.fetch_message(710984913616240650)
            trophies = []
            for key in (await self.bsconfig.guild(message.guild).clubs()).keys():
                tag = await self.bsconfig.guild(message.guild).clubs.get_raw(key, "tag")
                club = await self.ofcbsapi.get_club(tag)
                for member in club.members:
                    pair = []
                    pair.append(member.name)
                    pair.append(member.trophies)
                    pair.append(club.name)
                    trophies.append(pair)
            trophies = sorted(trophies, key=lambda x: x[1], reverse=True)
            messages = []
            msg = ""
            i = 1
            for trophy in trophies:
                if trophy == trophies[20] or trophy == trophies[40] or trophy == trophies[60] or trophy == trophies[
                    80] or trophy == trophies[100]:
                    messages.append(msg)
                    msg = ""
                msg += f"{i}. <:bstrophy:552558722770141204> {trophy[1]} **{trophy[0]}**({trophy[2]})\n"
                i = i + 1
            for m in messages:
                if m == messages[0]:
                    embed = discord.Embed(color=discord.Colour.gold(), title=f"{message.guild.name} leaderboard:",
                                          description=m)
                    await message.edit(embed=embed)
                elif m == messages[1]:
                    embed = discord.Embed(color=discord.Colour.gold(), description=m)
                    await message2.edit(embed=embed)
                elif m == messages[2]:
                    embed = discord.Embed(color=discord.Colour.gold(), description=m)
                    await message3.edit(embed=embed)
                elif m == messages[3]:
                    embed = discord.Embed(color=discord.Colour.gold(), description=m)
                    await message4.edit(embed=embed)
                elif m == messages[4]:
                    embed = discord.Embed(color=discord.Colour.gold(), description=m)
                    await message5.edit(embed=embed)

    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def blacklisted(self, ctx):
        """View all blacklisted people"""
        await ctx.trigger_typing()

        if len((await self.config.guild(ctx.guild).blacklisted()).keys()) < 1:
            return await ctx.send(
                embed=badEmbed(f"This server doesn't have anyone blacklisted!"))

        try:
            players = []
            keys = (await self.config.guild(ctx.guild).blacklisted()).keys()
            for key in keys:
                player = await self.ofcbsapi.get_player(key)
                players.append(player)
        except brawlstats.errors.RequestError as e:
            await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        msg = ""
        alertembed = False
        for plr in players:
            alert = False
            key = ""
            clubname = ""
            for k in (await self.config.guild(ctx.guild).blacklisted()).keys():
                if plr.tag.replace("#", "").lower() == k:
                    key = k

            player_in_club = "name" in plr.raw_data["club"]
            if player_in_club:
                clubname = plr.club.name
            else:
                clubname = "No club"

            await self.config.guild(ctx.guild).blacklisted.set_raw(key, 'ign', value=plr.name)
            await self.config.guild(ctx.guild).blacklisted.set_raw(key, 'club', value=clubname)

            clubs = []
            for keey in (await self.bsconfig.guild(ctx.guild).clubs()).keys():
                club = await self.bsconfig.guild(ctx.guild).clubs.get_raw(keey, "tag")
                clubs.append(club)

            if player_in_club:
                if plr.club.tag.strip("#") in clubs:
                    alert = True
                    alertembed = True

            keyforembed = "#" + key.upper()

            reason = await self.config.guild(ctx.guild).blacklisted.get_raw(key, "reason", default="")
            if alert:
                msg += f"--->{plr.name}({keyforembed}) <:bsband:600741378497970177> **{clubname}** Reason: {reason}<---\n"
            if not alert:
                msg += f"{plr.name}({keyforembed}) <:bsband:600741378497970177> **{clubname}** Reason: {reason}\n"

        if alertembed:
            await ctx.send(embed=discord.Embed(color=discord.Colour.red(), description=msg, title="Blacklist"))
        elif not alertembed:
            await ctx.send(embed=discord.Embed(color=discord.Colour.green(), description=msg, title="Blacklist"))

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @blacklisted.command(name="add")
    async def blacklist_add(self, ctx, tag: str, *, reason: str = ""):
        """
        Add a player to blacklist
        """
        await ctx.trigger_typing()

        tag = tag.lower().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        if tag in (await self.config.guild(ctx.guild).blacklisted()).keys():
            return await ctx.send(embed=badEmbed("This person is already blacklisted!"))

        try:
            player = await self.ofcbsapi.get_player(tag)
            player_in_club = "name" in player.raw_data["club"]
            if player_in_club:
                clubname = player.club.name
            else:
                clubname = "No club"
            result = {
                "ign": player.name,
                "club": clubname,
                "reason": reason
            }
            await self.config.guild(ctx.guild).blacklisted.set_raw(tag, value=result)
            await ctx.send(embed=goodEmbed(f"{player.name} was successfully blacklisted!"))

        except brawlstats.errors.NotFoundError as e:
            return await ctx.send(embed=badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send(
                f"**Something went wrong, please send a personal message to LA Modmail bot or try again!** ({e})")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @blacklisted.command(name="remove")
    async def blacklist_remove(self, ctx, tag: str):
        """
        Remove a person from blacklist
        """
        await ctx.trigger_typing()

        tag = tag.lower().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        try:
            ign = await self.config.guild(ctx.guild).blacklisted.get_raw(tag, "ign")
            await self.config.guild(ctx.guild).blacklisted.clear_raw(tag)
            await ctx.send(embed=goodEmbed(f"{ign} was successfully removed from this server's blacklist!"))
        except KeyError:
            await ctx.send(embed=badEmbed(f"{ign} isn't blacklisted in this server!"))

    @commands.command()
    async def unitedutil(self, ctx):
        for keey in (await self.bsconfig.guild(ctx.guild).clubs()).keys():
            await ctx.send(keey)
