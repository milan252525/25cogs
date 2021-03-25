import discord
from redbot.core import commands
from discord_slash import SlashCommand
from discord_slash import cog_ext, SlashContext

from typing import Union

class Slash(commands.Cog):
    def __init__(self, bot):
        if not hasattr(bot, "slash"):
            bot.slash = SlashCommand(bot, sync_commands=True)
        self.bot = bot

    @cog_ext.cog_slash(
        name="slashtest", 
        description="test command, might explode",
        guild_ids=[401883208511389716]
    )
    async def slash_test(self, ctx: SlashContext, member):
        await ctx.respond()
        await ctx.send(content="slash works")

    @cog_ext.cog_slash(
        name="ptest", 
        description="Get your BS stats",
        guild_ids=[401883208511389716]
    )
    async def p_test(self, ctx: SlashContext, member: Union[discord.Member, str] = None):
        await ctx.respond()
        await ctx.send(content=str(member))

        