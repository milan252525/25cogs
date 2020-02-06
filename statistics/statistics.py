import discord
from redbot.core import commands, Config, checks
import asyncio
import brawlstats

class Statistics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=424242)
        default_guild = {"tags": {}}
        self.config.register_guild(**default_guild)

    async def initialize(self):
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.OfficialAPI(ofcbsapikey["api_key"], is_async=True)

    @commands.command()
    @commands.guild_only()
    async def addclub(self, ctx, key : str, tag : str):
        await ctx.trigger_typing()

        tag = tag.lower().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        try:
            club = await self.ofcbsapi.get_club(tag)
            result = {
                "name": key,
                "tag": tag
            }
            key = key.lower()
            await self.config.guild(ctx.guild).tags.set_raw(key, value=result)
            await ctx.send(embed=discord.Embed(description=f"Club {club.name} successfully added.", color=discord.Colour.blue()))

        except brawlstats.errors.NotFoundError:
            await ctx.send(embed=discord.Embed(description="No club with this tag found.", color=discord.Colour.red()))

        except brawlstats.errors.RequestError as e:
            await ctx.send(embed=discord.Embed(f"BS API is offline, please try again later! ({str(e)})", color=discord.Colour.red()))

        except Exception as e:
            await ctx.send(f"**Something went wrong, please send a personal message to LA Modmail bot or try again!**** ({str(e)})")

    @commands.command()
    @commands.guild_only()
    async def removeclub(self, ctx, key : str):
        await ctx.trigger_typing()

        key = key.lower()

        try:
            await self.config.guild(ctx.guild).tags.clear_raw(key)
            await ctx.send(embed=discord.Embed(description=f"Club was successfully removed.", color=discord.Colour.blue()))
        except KeyError:
            await ctx.send(embed=discord.Embed(description=f"{tag} isn't saved in this server.", color=discord.Colour.red()))

    @commands.is_owner()
    @commands.command()
    async def collectinfo(self, ctx):
        for key in (await self.config.guild(ctx.guild).tags()).keys():
            tag = await self.config.guild(ctx.guild).tags.get_raw(key, "tag")
            club = await self.ofcbsapi.get_club(tag)
            mainembed = discord.Embed(title=club.name, color=discord.Colour.gold())
            mainembed.add_field(name="Members:", value=f"{len(club.members)}/100")
            await ctx.send(embed=mainembed)
            i = 0
            for member in club.members:
                msg = ""
                msg += f"**{member.name}**: "
                msg += f"Rank: {i+1}; "
                msg += f"Tag: {member.tag}; "
                msg += f"Role: {member.role.capitalize()}; "
                msg += f"Trophies: {member.trophies}."
                i = i + 1
                await ctx.send(msg)
        await ctx.send("Finished.")

    @commands.is_owner()
    @commands.command()
    async def summary(self, ctx, key : None):
        if key is None:
            totaltrophies = 0
            totalmembers = 0
            averagetrophies = 0
            lower10 = 0
            members = []
            for key in (await self.config.guild(ctx.guild).tags()).keys():
                tag = await self.config.guild(ctx.guild).tags.get_raw(key, "tag")
                club = await self.ofcbsapi.get_club(tag)
                totalmembers = totalmembers + len(club.members)
                for member in club.members:
                    members.add(member)
            for mem in members:
                totaltrophies = totaltrophies + mem.trophies
            for i in range(len(mem) - len(mem)//10, len(mem)):
                lower10 = lower10 + mem[i].trophies
            averagetrophies = totaltrophies//totalmembers
            embed = discord.Embed(color=discord.Colour.gold())
            embed.add_field(name="Total trophies:", value=totaltrophies)
            embed.add_field(name="Total members:", value=totalmembers)
            embed.add_field(name="Average trophies:", value=averagetrophies)
            embed.add_field(name="Lower 10% average:", value=lower10//(len(mem) - len(mem)//10))
            await ctx.send(embed=embed)
        elif key is not None:
            tag = await self.config.guild(ctx.guild).tags.get_raw(key, "tag")
            club = await self.ofcbsapi.get_club(tag)
            for i in range(len(club.members) - len(club.members)//10, len(club.members)):
                lower10 = lower10 + club.members[i].trophies
            embed = discord.Embed(color=discord.Colour.gold())
            embed.add_field(name="Total trophies:", value=club.trophies)
            embed.add_field(name="Total members:", value=club.members)
            embed.add_field(name="Average trophies:", value=club.trophies//club.members)
            embed.add_field(name="Lower 10% average:", value=lower10 // (len(club.members) - len(club.members)//10))
            await ctx.send(embed=embed)