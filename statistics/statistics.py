import discord
from discord.ext import tasks

from redbot.core import commands, Config, checks
from redbot.core.utils.menus import menu, prev_page, next_page

import asyncio
import brawlstats
import clashroyale


class Statistics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=42424269)
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

    def get_bs_config(self):
        if self.bsconfig is None:
            self.bsconfig = Config.get_conf(None, identifier=5245652, cog_name="BrawlStarsCog")
        return self.bsconfig

    @commands.is_owner()
    @commands.command()
    async def summary(self, ctx, key:str=None):
        if key is None:
            totaltrophies = 0
            averagetrophies = 0
            lower10 = 0
            members = []
            for key in (await self.get_bs_config().guild(ctx.guild).clubs()).keys():
                tag = await self.get_bs_config().guild(ctx.guild).clubs.get_raw(key, "tag")
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
            tag = await self.get_bs_config().guild(ctx.guild).clubs.get_raw(key, "tag")
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
            for key in (await self.get_bs_config().guild(ctx.guild).clubs()).keys():
                tag = await self.get_bs_config().guild(ctx.guild).clubs.get_raw(key, "tag")
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
            tag = await self.get_bs_config().guild(ctx.guild).clubs.get_raw(key, "tag")
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

    @tasks.loop(minutes=80)
    async def lbrenewalbd(self):
        channel = self.bot.get_channel(691278145185251328)
        if channel is not None:
            message = await channel.fetch_message(691296279157801050)
            trophies = []
            for key in (await self.get_bs_config().guild(message.guild).clubs()).keys():
                tag = await self.get_bs_config().guild(message.guild).clubs.get_raw(key, "tag")
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
