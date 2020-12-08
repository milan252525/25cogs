from .statistics import Statistics

async def setup(bot):
  cog = Statistics(bot)
  bot.add_cog(cog)
