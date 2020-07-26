import discord

from redbot.core import commands, Config, checks
from bs.utils import goodEmbed, badEmbed

import asyncio
import brawlstats
from typing import Union

class Achievements(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=42696969)
        default_user = {"carrier": False,
                        "teamwork": False,
                        "assassin": False,
                        "massacre": False,
                        "bounty": False,
                        "thief": False,
                        "close": False,
                        "guardian": False,
                        "deadlock": False,
                        "turbo": False,
                        "pro": False,
                        "stale": False,
                        "op": False,
                        "clutch": False,
                        "nailb": False,
                        "zoned": False,
                        "domination": False,
                        "trident": False,
                        "over": False,
                        "survivalist": False,
                        "after": False,
                        "pinch": False,
                        "dynamic": False,
                        "shut": False,
                        "robo": False,
                        "defender": False,
                        "city": False,
                        "draw": False,
                        "max": False,
                        "brawlm": False,
                        "brawll": False,
                        "portrait": False,
                        "landscape": False,
                        "global": False,
                        "bling": False,
                        "celeb": False,
                        "beast": False,
                        "god": False,
                        "expa": False,
                        "expp": False,
                        "expg": False,
                        "trophya": False,
                        "trophyp": False,
                        "trophyg": False,
                        "tvta": False,
                        "tvtp": False,
                        "tvtg": False,
                        "soloa": False,
                        "solop": False,
                        "solog": False,
                        "duoa": False,
                        "duop": False,
                        "duog": False,
                        "ppa": False,
                        "ppp": False,
                        "ppg": False}
        self.config.register_user(**default_user)

    async def initialize(self):
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.Client(ofcbsapikey["api_key"], is_async=True)

    @commands.command(aliases=['a'])
    async def achievements(self, ctx, *, member: Union[discord.Member, str] = None):
        await ctx.trigger_typing()

        member = ctx.author if member is None else member

        if not isinstance(member, discord.Member):
            try:
                member = self.bot.get_user(int(member))
            except ValueError:
                member = discord.utils.get(ctx.guild.members, name=member)

        aembed = discord.Embed(color=discord.Colour.blue(), title="Achievements", description=f"{str(member)}'s achievements")
        aembed.set_image(url="https://cdn.discordapp.com/attachments/472117791604998156/736896897872035960/0a00e865c445d42dfb9f64bedfab8cf8.png")

        gg = ""
        if await self.config.user(member).carrier():
            gg = gg + "Carrier\n"
        if await self.config.user(member).teamwork():
            gg = gg + "Teamwork\n"
        if gg != "":
            aembed.add_field(name="Gem Grab", value=gg)

        await ctx.send(embed=aembed)

    @commands.command(aliases=['aa'])
    async def addachievement(self, ctx, keyword, member: discord.Member):
        await ctx.trigger_typing()

        try:
            for k in await self.config.user(member):
                if k == keyword:
                    await self.config.user(member).k.set(True)

            await ctx.send(embed=goodEmbed(f"Achievement {keyword} successfully registered for the user {str(member)}."))
        except Exception as e:
            await ctx.send(embed=badEmbed(f"An error occurred: {e}."))
