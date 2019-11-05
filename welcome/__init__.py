from .welcome import Welcome

async def setup(bot):
  cog = Welcome(bot)
  await cog.initialize()
  bot.add_cog(cog)