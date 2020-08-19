from .achievementsspain import AchievementsSpain

async def setup(bot):
  cog = AchievementsSpain(bot)
  await cog.initialize()
  bot.add_cog(cog)