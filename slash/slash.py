import discord
from redbot.core import commands
from discord_slash import SlashCommand
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import remove_all_commands

from typing import Union

class Slash(commands.Cog):
    def __init__(self, bot):
        if not hasattr(bot, "slash"):
            bot.slash = SlashCommand(bot, sync_on_cog_reload=True)
        self.bot = bot

    def cog_unload(self):
        self.bot.slash.remove_cog_commands(self)

    @cog_ext.cog_slash(
        name="slashtest", 
        description="Test command, might explode!",
        guild_ids=[401883208511389716]
    )
    async def slash_test(self, ctx: SlashContext):
        await ctx.respond()
        await ctx.send(content="Slash works!")

    @cog_ext.cog_slash(
        name="ptest", 
        description="Get your BS stats",
        guild_ids=[401883208511389716]
    )
    async def p_test(self, ctx: SlashContext, member = None):
        await ctx.respond(eat=False)
        msg = await ctx.send(content=str(ctx.message))
        msg.content = f"/profile {member}" if member is not None else "/profile"
        msg.author = ctx.author
        await self.bot.process_commands(msg)

        