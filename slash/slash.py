import discord
from redbot.core import commands
from discord_slash import SlashCommand
from discord_slash import cog_ext, SlashContext

class Slash(commands.Cog):
    def __init__(self, bot):
        bot.slash = SlashCommand(bot, override_type=True, sync_commands=True)
        self.bot = bot

    @cog_ext.cog_slash(name="test")
    async def _test(self, ctx: SlashContext):
        embed = discord.Embed(title="embed test")
        await ctx.send(content="test", embeds=[embed])