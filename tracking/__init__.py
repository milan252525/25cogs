from .tracking import Tracking

async def setup(bot):
  cog = Tracking(bot)
  await cog.initialize()
  bot.add_cog(cog)
