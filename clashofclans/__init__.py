from .clashofclans import ClashOfClansCog

async def setup(bot):
  cog = ClashOfClansCog(bot)
  await cog.initialize()
  bot.add_cog(cog)