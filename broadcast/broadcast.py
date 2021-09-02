import discord
from redbot.core import commands, Config, checks

from typing import Union
import asyncio


class Broadcast(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=20925250209)
        default_global = {"subscriptions" : {}}
        self.config.register_global(**default_global)

    @commands.Cog.listener()
    async def on_message(self, msg):
        return

    @commands.guild_only()
    @commands.is_owner()
    @commands.command()
    async def subscribe(self, ctx, broadcast_name:str):

        await ctx.send("Done!")
    