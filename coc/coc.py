import discord
import coc


class ClashOfClansCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=42136942)
        default_user = {"tag": None}
        self.config.register_user(**default_user)
        default_guild = {"clans": {}}
        self.config.register_guild(**default_guild)

    async def initialize(self):
        self.cocapi = coc.login("pazuzu636@gmail.com", "Milanisbae")

    @commands.command()
    async def getCOCname(self, ctx, tag):
        player = await self.cocapi.get_player(tag)

        await ctx.send(player.name)