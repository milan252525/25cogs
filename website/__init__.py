from .wesbite import Website

async def setup(bot):
  cog = Website(bot)
  bot.add_cog(cog)