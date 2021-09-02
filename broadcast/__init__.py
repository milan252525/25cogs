from .broadcast import Broadcast

async def setup(bot):
  cog = Broadcast(bot)
  bot.add_cog(cog)
