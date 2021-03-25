from .slash import Slash

async def setup(bot):
  cog = Slash(bot)
  bot.add_cog(cog)
