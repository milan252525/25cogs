from .challenges import Challenges

async def setup(bot):
  cog = Challenges(bot)
  await cog.initialize()
  bot.add_cog(cog)
