from .tools import Tools

async def setup(bot):
  cog = Tools(bot)
  bot.add_cog(cog)
