from .blacklist import Blacklist

async def setup(bot):
  cog = Blacklist(bot)
  await cog.initialize()
  bot.add_cog(cog)
