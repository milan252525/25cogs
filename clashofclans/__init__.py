from .clashofclans import ClashOfClansCog

async def setup(bot):
  cog = ClashOfClansCog(bot)
  bot.add_cog(cog)