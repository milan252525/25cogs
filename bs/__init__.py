from .bs import BrawlStarsCog

async def setup(bot):
  cog = BrawlStarsCog(bot)
  await cog.initialize()
  bot.add_cog(cog)
