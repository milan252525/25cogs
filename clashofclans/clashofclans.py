import discord
import coc
from redbot.core import commands, Config


class ClashOfClansCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=42136942)
        default_user = {"tag": None}
        self.config.register_user(**default_user)
        default_guild = {"clans": {}}
        self.config.register_guild(**default_guild)
        self.cocapi = coc.login("pazuzu636@gmail.com", "Milanisbae", client=coc.Client)

    async def initialize(self):
        cocapilogin = await self.bot.get_shared_api_tokens("coclogin")
        if cocapilogin["login"] is None:
            raise ValueError("The Clash of Clans API login has not been set.")
        cocapipassword = await self.bot.get_shared_api_tokens("cocpass")
        if cocapipassword["password"] is None:
            raise ValueError("The Clash of Clans API password has not been set.")
        self.cocapi = coc.login(cocapilogin, cocapipassword, client=coc.Client)

    @commands.command()
    async def getCOCname(self, ctx, tag):
        player = await self.cocapi.get_player(tag)

        await ctx.send(player.name)