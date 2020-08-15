import discord
import httpx

from random import choice
from redbot.core import commands, Config
from bs.utils import badEmbed, goodEmbed
from redbot.core.utils.menus import menu, prev_page, next_page

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

    @commands.guild_only()
    @commands.group(aliases=['coc_clan'], invoke_without_command=True)
    async def coc_clans(self, ctx):
        """View all clans saved in a server"""
        if len((await self.config.guild(ctx.guild).clans()).keys()) < 1:
            return await ctx.send(
                embed=badEmbed(f"This server has no clans saved. Save a club by using {ctx.prefix}coc_clan add!"))

        saved_clans = await self.config.guild(ctx.guild).clans()

        try:
            clans = []
            keys = saved_clans.keys()
            for k in keys:
                clan = self.apirequest("clans/%23" + saved_clans[k]['tag'])
                clans.append(clan)

            embedFields = []

            clans = sorted(clans, key=lambda sort: (sort['trophies']))
            
            for i in range(len(clans)):
                key = ""
                for k in saved_clans.keys():
                    if clans[i].tag.replace("#", "") == saved_clans[k]['tag']:
                        key = k

                saved_clans[key]['lastMemberCount'] = clan[i]['members']
                saved_clans[key]['lastRequirement'] = clan[i]['reqiredTrophies']
                saved_clans[key]['lastPoints'] = clan[i]['clanPoints']
                saved_clans[key]['lastPosition'] = i
                saved_clans[key]['lastVersusPoints'] = clans[i]['clanVersusPoints']

                info = saved_clans[key]["info"] if "info" in saved_clans[key] else ""

                e_name = f"<:bsband:600741378497970177> {clans[i]['name']} [{key}] {clans[i]['tag']} {info}"
                e_value = f"🏆`{clans[i]['clanPoints']}` 🏆`{clans[i]['clanVersusPoints']}`"
                e_value += f"`{clans[i]['requiredTrophies']}+` <:icon_gameroom:553299647729238016>`{clans[i]['members']}`"
                embedFields.append([e_name, e_value])

            await self.config.guild(ctx.guild).set_raw("clans", value=saved_clans)


            colour = choice([discord.Colour.green(),
                             discord.Colour.blue(),
                             discord.Colour.purple(),
                             discord.Colour.orange(),
                             discord.Colour.red(),
                             discord.Colour.teal()])

            embedsToSend = []
            for i in range(0, len(embedFields), 8):
                embed = discord.Embed(colour=colour)
                embed.set_author(
                    name=f"{ctx.guild.name} clans",
                    icon_url=ctx.guild.icon_url)
                page = (i // 8) + 1
                footer = f"[{page}/{len(embedFields)//8+1}]"
                embed.set_footer(text=footer)
                for e in embedFields[i:i + 8]:
                    embed.add_field(name=e[0], value=e[1], inline=False)
                embedsToSend.append(embed)

            if len(embedsToSend) > 1:
                await menu(ctx, embedsToSend, {"⬅": prev_page, "➡": next_page, }, timeout=2000)
            elif len(embedsToSend) == 1:
                await ctx.send(embed=embedsToSend[0])
            else:
                await ctx.send("No clans found!")

        except ZeroDivisionError as e:
            return await ctx.send(
                "**Something went wrong, please send a personal message to LA Modmail bot or try again!**")

    @coc_clans.command(name="add")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def coc_clan_add(self, ctx, key: str, tag: str):
        await ctx.trigger_typing()

        if key in (await self.config.guild(ctx.guild).clans()).keys():
            return await ctx.send(embed=badEmbed("This clan is already saved!"))

        try:
            clan = self.apirequest("clans/%23" + tag.replace("#", ""))
            result = {
                "name": clan['name'],
                "nick": key.title(),
                "tag": clan['tag'].replace("#", ""),
                "lastMemberCount": clan['members'],
                "lastRequirement": clan['requiredTrophies'],
                "lastPoints": clan['clanPoints'],
                "lastVersusPoints": clan['clanVersusPoints'],
                "info": ""
            }
            key = key.lower()
            await self.config.guild(ctx.guild).clans.set_raw(key, value=result)
            await ctx.send(embed=goodEmbed(f"{clan['name']} was successfully saved in this server!"))

        except Exception as e:
            return await ctx.send(f"**Something went wrong: {str(e)}.**")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @coc_clans.command(name="remove")
    async def clubs_remove(self, ctx, key: str):
        await ctx.trigger_typing()
        key = key.lower()

        try:
            name = await self.config.guild(ctx.guild).clans.get_raw(key, "name")
            await self.config.guild(ctx.guild).clans.clear_raw(key)
            await ctx.send(embed=goodEmbed(f"{name} was successfully removed from this server!"))
        except KeyError:
            await ctx.send(embed=badEmbed(f"{key.title()} isn't saved club!"))
