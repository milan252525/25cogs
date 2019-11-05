from .cr import Ladder

async def setup(bot):
  cog = Ladder(bot)
  bot.add_cog(cog)
