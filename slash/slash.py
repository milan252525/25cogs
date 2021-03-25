import discord
from redbot.core import commands
from discord_slash import SlashCommand
from discord_slash import cog_ext, SlashContext
import logging

class Slash(commands.Cog):
    def __init__(self, bot):
        if not hasattr(bot, "slash"):
            logging.error("condition triggered")
            bot.slash = SlashCommand(bot, sync_commands=True)
        self.bot = bot


    @cog_ext.cog_slash(name="test")
    async def _test(self, ctx: SlashContext):
        embed = discord.Embed(title="embed test")
        await ctx.send(content="test", embeds=[embed])

    @cog_ext.cog_slash(
        name="slashtest", 
        description="test command, might explode",
        guild_ids=[401883208511389716]
    )
    async def slash_test(self, ctx: SlashContext):
        await ctx.respond()
        await ctx.send(content="slash works")