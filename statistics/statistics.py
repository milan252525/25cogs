from redbot.core import commands, Config, checks


class Statistics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=42424269)

    @commands.command()
    async def trophylb(self, ctx):
        await ctx.send("Looks like this command's pending deletion. Refer to https://laclubs.net/lb to get the up-to-date leaderboard!")
