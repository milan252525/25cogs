import discord

from redbot.core import commands, Config, checks
from bs.utils import goodEmbed, badEmbed

import asyncio
import brawlstats
from typing import Union

class Achievements(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=42696969)
        default_user = {"carrier": False,
                        "teamwork": False,
                        "assassin": False,
                        "massacre": False,
                        "bounty": False,
                        "thief": False,
                        "close": False,
                        "guardian": False,
                        "deadlock": False,
                        "turbo": False,
                        "pro": False,
                        "stale": False,
                        "op": False,
                        "clutch": False,
                        "nailb": False,
                        "zoned": False,
                        "domination": False,
                        "trident": False,
                        "over": False,
                        "survivalist": False,
                        "after": False,
                        "pinch": False,
                        "dynamic": False,
                        "shut": False,
                        "robo": False,
                        "defender": False,
                        "city": False,
                        "draw": False,
                        "max": False,
                        "brawlm": False,
                        "brawll": False,
                        "portrait": False,
                        "landscape": False,
                        "globalog": False,
                        "bling": False,
                        "celeb": False,
                        "beast": False,
                        "god": False,
                        "expa": False,
                        "expp": False,
                        "expg": False,
                        "trophya": False,
                        "trophyp": False,
                        "trophyg": False,
                        "tvta": False,
                        "tvtp": False,
                        "tvtg": False,
                        "soloa": False,
                        "solop": False,
                        "solog": False,
                        "duoa": False,
                        "duop": False,
                        "duog": False,
                        "ppa": False,
                        "ppp": False,
                        "ppg": False}
        self.config.register_user(**default_user)

    async def initialize(self):
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.Client(ofcbsapikey["api_key"], is_async=True)

    @commands.command(aliases=['a'])
    async def achievements(self, ctx, *, member: Union[discord.Member, str] = None):
        if ctx.guild.id != 401883208511389716:
            return await ctx.send(embed=badEmbed("Can't use this here, sorry."))

        await ctx.trigger_typing()

        member = ctx.author if member is None else member

        if not isinstance(member, discord.Member):
            try:
                member = self.bot.get_user(int(member))
            except ValueError:
                member = discord.utils.get(ctx.guild.members, name=member)

        aembed = discord.Embed(color=discord.Colour.blue(), title="Achievements", description=f"{str(member)}'s achievements:")
        aembed.set_thumbnail(url="https://cdn.discordapp.com/attachments/472117791604998156/736896897872035960/0a00e865c445d42dfb9f64bedfab8cf8.png")

        gg = ""
        if await self.config.user(member).carrier():
            gg = gg + "Carrier\n"
        if await self.config.user(member).teamwork():
            gg = gg + "Teamwork\n"
        if gg != "":
            aembed.add_field(name="Gem Grab", value=gg)

        bounty = ""
        if await self.config.user(member).assassin():
            bounty = bounty + "Assassin\n"
        if await self.config.user(member).massacre():
            bounty = bounty + "Massacre\n"
        if await self.config.user(member).bounty():
            bounty = bounty + "Bounty Hunter\n"
        if bounty != "":
            aembed.add_field(name="Bounty", value=bounty)

        heist = ""
        if await self.config.user(member).thief():
            heist = heist + "Thief\n"
        if await self.config.user(member).close():
            heist = heist + "Close Call\n"
        if await self.config.user(member).guardian():
            heist = heist + "Guardian\n"
        if await self.config.user(member).deadlock():
            heist = heist + "Deadlock\n"
        if heist != "":
            aembed.add_field(name="Heist", value=heist)

        bb = ""
        if await self.config.user(member).turbo():
            bb = bb + "Turbo\n"
        if await self.config.user(member).pro():
            bb = bb + "Pro Ball\n"
        if bb != "":
            aembed.add_field(name="Brawl Ball", value=bb)

        siege = ""
        if await self.config.user(member).stale():
            siege = siege + "Stalemate\n"
        if await self.config.user(member).op():
            siege = siege + "OP Bot\n"
        if await self.config.user(member).clutch():
            siege = siege + "Clutch\n"
        if siege != "":
            aembed.add_field(name="Siege", value=siege)

        hz = ""
        if await self.config.user(member).nailb():
            hz = hz + "Nail Biter\n"
        if await self.config.user(member).zoned():
            hz = hz + "Zoned Out\n"
        if await self.config.user(member).domination():
            hz = hz + "Domination\n"
        if hz != "":
            aembed.add_field(name="Hot Zone", value=hz)

        ss = ""
        if await self.config.user(member).trident():
            ss = ss + "Trident\n"
        if await self.config.user(member).over():
            ss = ss + "Overload\n"
        if await self.config.user(member).survivalist():
            ss = ss + "Survivalist\n"
        if await self.config.user(member).after():
            ss = ss + "Afterlife\n"
        if ss != "":
            aembed.add_field(name="Solo Showdown", value=ss)

        ds = ""
        if await self.config.user(member).pinch():
            ds = ds + "Pinched\n"
        if await self.config.user(member).dynamic():
            ds = ds + "Dynamic Duo\n"
        if ds != "":
            aembed.add_field(name="Duo Showdown", value=ds)

        events = ""
        if await self.config.user(member).shut():
            events = events + "Shutdown\n"
        if await self.config.user(member).robo():
            events = events + "Robo Destroyer\n"
        if await self.config.user(member).defender():
            events = events + "Defender\n"
        if await self.config.user(member).city():
            events = events + "City Protector\n"
        if events != "":
            aembed.add_field(name="Events", value=events)

        misc = ""
        if await self.config.user(member).draw():
            misc = misc + "Draw Star\n"
        if await self.config.user(member).max():
            misc = misc + "Max Power\n"
        if await self.config.user(member).brawlm():
            misc = misc + "Brawl Master\n"
        if await self.config.user(member).brawll():
            misc = misc + "Brawl Legend\n"
        if await self.config.user(member).portrait():
            misc = misc + "Portrait OG\n"
        if await self.config.user(member).landscape():
            misc = misc + "Landscape OG\n"
        if await self.config.user(member).globalog():
            misc = misc + "Global OG\n"
        if await self.config.user(member).bling():
            misc = misc + "Bling\n"
        if await self.config.user(member).celeb():
            misc = misc + "Celebrity\n"
        if await self.config.user(member).beast():
            misc = misc + "Beast Brawler\n"
        if await self.config.user(member).god():
            misc = misc + "God Brawler\n"
        if misc != "":
            aembed.add_field(name="Miscellaneous", value=misc)

        exp = ""
        if await self.config.user(member).expa():
            exp = exp + "Exp Amateur\n"
        elif await self.config.user(member).expp():
            exp = exp + "Exp Pro\n"
        elif await self.config.user(member).expg():
            exp = exp + "Exp God\n"
        if exp != "":
            aembed.add_field(name="Experience Levels", value=exp)

        troph = ""
        if await self.config.user(member).trophya():
            troph = troph + "Trophy Amateur\n"
        elif await self.config.user(member).trophyp():
            troph = troph + "Trophy Pro\n"
        elif await self.config.user(member).trophyg():
            troph = troph + "Trophy God\n"
        if troph != "":
            aembed.add_field(name="Trophies", value=troph)

        tvt = ""
        if await self.config.user(member).tvta():
            tvt = tvt + "3v3 Amateur\n"
        elif await self.config.user(member).tvtp():
            tvt = tvt + "3v3 Pro\n"
        elif await self.config.user(member).tvtg():
            tvt = tvt + "3v3 God\n"
        if tvt != "":
            aembed.add_field(name="3v3 Wins", value=tvt)

        solo = ""
        if await self.config.user(member).soloa():
            solo = solo + "Solo Amateur\n"
        elif await self.config.user(member).solop():
            solo = solo + "Solo Pro\n"
        elif await self.config.user(member).solog():
            solo = solo + "Solo God\n"
        if solo != "":
            aembed.add_field(name="Solo Showdown", value=solo)

        duo = ""
        if await self.config.user(member).duoa():
            duo = duo + "Duo Amateur\n"
        elif await self.config.user(member).duop():
            duo = duo + "Duo Pro\n"
        elif await self.config.user(member).duog():
            duo = duo + "Duo God\n"
        if duo != "":
            aembed.add_field(name="Duo Showdown", value=duo)

        pp = ""
        if await self.config.user(member).ppa():
            pp = pp + "PowerPlay Amateur\n"
        elif await self.config.user(member).ppp():
            pp = pp + "PowerPlay Pro\n"
        elif await self.config.user(member).ppg():
            pp = pp + "PowerPlay God\n"
        if pp != "":
            aembed.add_field(name="Power Play Points", value=pp)

        return await ctx.send(embed=aembed)

    @commands.command(aliases=['aa'])
    async def addachievement(self, ctx, keyword, member: discord.Member):
        if ctx.guild.id != 401883208511389716:
            return await ctx.send(embed=badEmbed("Can't use this here, sorry."))

        rolesna = ctx.guild.get_role(564552111875162112)
        if not ctx.author.guild_permissions.kick_members and rolesna not in ctx.author.roles:
            return await ctx.send(embed=badEmbed("You can't use this, sorry."))

        try:
            achievements = self.config.user(member)
            achievements[keyword] = True
            self.config.user(member).set(achievements)
            return await ctx.send(embed=goodEmbed(f"Achievement {keyword.capitalize()} successfully added to {str(member)}."))
        except Exception as e:
            return await ctx.send(embed=badEmbed(f"Something went wrong: {e}."))
