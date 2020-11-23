from .website import Website

async def setup(bot):
  cog = Website(bot)
  bot.add_cog(cog)