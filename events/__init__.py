from .events import Events

async def setup(bot):
  cog = Events(bot)
  bot.add_cog(cog)
