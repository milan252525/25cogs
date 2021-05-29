from .slash import Slash
from discord_slash import SlashCommand

async def setup(bot):
  if not hasattr(bot, "slash"):
    bot.slash = SlashCommand(bot, sync_on_cog_reload=True)
  cog = Slash(bot)
  bot.add_cog(cog)
  await bot.slash.sync_all_commands()
