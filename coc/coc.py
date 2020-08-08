import discord
import httpx
from redbot.core import commands, Config


class ClashOfClansCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=42136942)
        default_user = {"tag": None}
        self.config.register_user(**default_user)
        default_guild = {"clans": {}}
        self.config.register_guild(**default_guild)
        self.baseurl = "https://api.clashofclans.com/v1/"

    async def initialize(self):
        cockey = await self.bot.get_shared_api_tokens("cocapi")
        token = cockey["api_key"]
        if token is None:
            raise ValueError("CoC API key has not been set.")
        self.headers = {
            "authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def apirequest(self, url: str):
        url = self.baseurl + url
        response = httpx.get(url=url, headers=self.headers, timeout=20)
        return response.json()

    @commands.command()
    async def getclantest(self, ctx, tag: str):
        tag = "clans/%23" + tag.replace("#", "")

        try:
            clan_json = self.apirequest(tag)
        except Exception as e:
            return await ctx.send(e)

        await ctx.send("All went good.")