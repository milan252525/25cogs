from .achievements import Achievements

async def setup(bot):
  cog = Achievements(bot)
  await cog.initialize()
  bot.add_cog(cog)