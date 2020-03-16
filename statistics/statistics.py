import discord
from redbot.core import commands, Config, checks
import asyncio
import brawlstats

class Statistics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bsconfig = Config.get_conf(None, identifier=5245652, cog_name="BrawlStarsCog")

    async def initialize(self):
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.OfficialAPI(ofcbsapikey["api_key"], is_async=True)

    @commands.is_owner()
    @commands.command()
    async def summary(self, ctx, key:str=None):
        if key is None:
            totaltrophies = 0
            averagetrophies = 0
            lower10 = 0
            members = []
            for key in (await self.config.guild(ctx.guild).tags()).keys():
                tag = await self.config.guild(ctx.guild).tags.get_raw(key, "tag")
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
            tag = await self.config.guild(ctx.guild).tags.get_raw(key, "tag")
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
            msg = ""
            for trophy in trophies:
                if trophy == trophies[20]:
                    break
                msg += f"{trophy[1]} {trophy[0]}({trophy[2]})\n"
            embed = discord.Embed(color=discord.Colour.gold(), title=f"{ctx.guild.name} leaderboard:", description=msg)
            await ctx.send(embed=embed)
        elif key is not None:
            tag = await self.bsconfig.guild(ctx.guild).clubs.get_raw(key, "tag")
            club = await self.ofcbsapi.get_club(tag)
            msg = ""
            for member in club.members:
                if member == club.members[20]:
                    break
                msg += f"{member.trophies} {member.name}\n"
            embed = discord.Embed(color=discord.Colour.gold(), title=f"{club.name} leaderboard:", description=msg)
            await ctx.send(embed=embed)
