from .slash import Slash
from discord_slash import SlashCommand

async def setup(bot):
  bot = SlashCommand(bot, override_type = True)
  cog = Slash(bot)
  bot.add_cog(cog)
