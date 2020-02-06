from .statistics import Statistics

async def setup(bot):
  cog = Statistics(bot)
  await cog.initialize()
  bot.add_cog(cog)
