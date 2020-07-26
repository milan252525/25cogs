import discord

from redbot.core import commands, Config, checks
from bs.utils import goodEmbed, badEmbed

import asyncio
import brawlstats
from typing import Union
from fuzzywuzzy import process

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
                        "trioa": False,
                        "triop": False,
                        "triog": False,
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
        """Check yours or other person's achievements"""
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
            aembed.add_field(name="Gem Grab", value=gg, inline=False)

        bounty = ""
        if await self.config.user(member).assassin():
            bounty = bounty + "Assassin\n"
        if await self.config.user(member).massacre():
            bounty = bounty + "Massacre\n"
        if await self.config.user(member).bounty():
            bounty = bounty + "Bounty Hunter\n"
        if bounty != "":
            aembed.add_field(name="Bounty", value=bounty, inline=False)

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
            aembed.add_field(name="Heist", value=heist, inline=False)

        bb = ""
        if await self.config.user(member).turbo():
            bb = bb + "Turbo\n"
        if await self.config.user(member).pro():
            bb = bb + "Pro Ball\n"
        if bb != "":
            aembed.add_field(name="Brawl Ball", value=bb, inline=False)

        siege = ""
        if await self.config.user(member).stale():
            siege = siege + "Stalemate\n"
        if await self.config.user(member).op():
            siege = siege + "OP Bot\n"
        if await self.config.user(member).clutch():
            siege = siege + "Clutch\n"
        if siege != "":
            aembed.add_field(name="Siege", value=siege, inline=False)

        hz = ""
        if await self.config.user(member).nailb():
            hz = hz + "Nail Biter\n"
        if await self.config.user(member).zoned():
            hz = hz + "Zoned Out\n"
        if await self.config.user(member).domination():
            hz = hz + "Domination\n"
        if hz != "":
            aembed.add_field(name="Hot Zone", value=hz, inline=False)

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
            aembed.add_field(name="Solo Showdown", value=ss, inline=False)

        ds = ""
        if await self.config.user(member).pinch():
            ds = ds + "Pinched\n"
        if await self.config.user(member).dynamic():
            ds = ds + "Dynamic Duo\n"
        if ds != "":
            aembed.add_field(name="Duo Showdown", value=ds, inline=False)

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
            aembed.add_field(name="Events", value=events, inline=False)

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
            aembed.add_field(name="Miscellaneous", value=misc, inline=False)

        exp = ""
        if await self.config.user(member).expa():
            exp = exp + "Exp Amateur\n"
        elif await self.config.user(member).expp():
            exp = exp + "Exp Pro\n"
        elif await self.config.user(member).expg():
            exp = exp + "Exp God\n"
        if exp != "":
            aembed.add_field(name="Experience Levels", value=exp, inline=False)

        troph = ""
        if await self.config.user(member).trophya():
            troph = troph + "Trophy Amateur\n"
        elif await self.config.user(member).trophyp():
            troph = troph + "Trophy Pro\n"
        elif await self.config.user(member).trophyg():
            troph = troph + "Trophy God\n"
        if troph != "":
            aembed.add_field(name="Trophies", value=troph, inline=False)

        tvt = ""
        if await self.config.user(member).trioa():
            tvt = tvt + "3v3 Amateur\n"
        elif await self.config.user(member).triop():
            tvt = tvt + "3v3 Pro\n"
        elif await self.config.user(member).triog():
            tvt = tvt + "3v3 God\n"
        if tvt != "":
            aembed.add_field(name="3v3 Wins", value=tvt, inline=False)

        solo = ""
        if await self.config.user(member).soloa():
            solo = solo + "Solo Amateur\n"
        elif await self.config.user(member).solop():
            solo = solo + "Solo Pro\n"
        elif await self.config.user(member).solog():
            solo = solo + "Solo God\n"
        if solo != "":
            aembed.add_field(name="Solo Showdown", value=solo, inline=False)

        duo = ""
        if await self.config.user(member).duoa():
            duo = duo + "Duo Amateur\n"
        elif await self.config.user(member).duop():
            duo = duo + "Duo Pro\n"
        elif await self.config.user(member).duog():
            duo = duo + "Duo God\n"
        if duo != "":
            aembed.add_field(name="Duo Showdown", value=duo, inline=False)

        pp = ""
        if await self.config.user(member).ppa():
            pp = pp + "PowerPlay Amateur\n"
        elif await self.config.user(member).ppp():
            pp = pp + "PowerPlay Pro\n"
        elif await self.config.user(member).ppg():
            pp = pp + "PowerPlay God\n"
        if pp != "":
            aembed.add_field(name="Power Play Points", value=pp, inline=False)

        return await ctx.send(embed=aembed)

    @commands.command(aliases=['aa'])
    async def addachievement(self, ctx, member: discord.Member, keyword):
        """Add or remove an achievement from a person"""
        if ctx.guild.id != 401883208511389716 and ctx.channel.id != 555662656736985090 and ctx.channel.id != 472117791604998156:
            return await ctx.send(embed=discord.Embed(color=discord.Colour.red(), description="**Can't use this here, sorry.**"))

        rolesna = ctx.guild.get_role(564552111875162112)
        if not ctx.author.guild_permissions.kick_members and rolesna not in ctx.author.roles:
            return await ctx.send(embed=discord.Embed(color=discord.Colour.red(), description="**You can't use this, sorry.**"))

        keys = await self.config.user(member).all()
        keyword = process.extract(keyword, keys.keys(), limit=1)
        keyword = keyword[0][0]

        try:
            if await self.config.user(member).get_raw(keyword):
                await self.config.user(member).set_raw(keyword, value=False)
                roles = await self.checkforroles(member)
                return await ctx.send(embed=discord.Embed(color=discord.Colour.green(), description=f"**Achievement {keyword} was successfully removed from {str(member)}.\n{roles}**"))
            if not await self.config.user(member).get_raw(keyword):
                await self.config.user(member).set_raw(keyword, value=True)
                roles = await self.checkforroles(member)
                return await ctx.send(embed=discord.Embed(color=discord.Colour.green(), description=f"**Achievement {keyword} was successfully added to {str(member)}.\n{roles}**"))
        except Exception as e:
            return await ctx.send(embed=discord.Embed(color=discord.Colour.red(), description=f"**Something went wrong: {e}.**"))

    @commands.command(aliases=['multi'])
    async def addachievements(self, ctx, member: discord.Member, *keywords):
        """Add or remove several achievements from a person"""
        if ctx.guild.id != 401883208511389716 and ctx.channel.id != 555662656736985090 and ctx.channel.id != 472117791604998156:
            return await ctx.send(embed=discord.Embed(color=discord.Colour.red(), description="**Can't use this here, sorry.**"))

        rolesna = ctx.guild.get_role(564552111875162112)
        if not ctx.author.guild_permissions.kick_members and rolesna not in ctx.author.roles:
            return await ctx.send(embed=discord.Embed(color=discord.Colour.red(), description="**You can't use this, sorry.**"))

        msg = ""
        for keyword in keywords:
            keys = await self.config.user(member).all()
            keyword = process.extract(keyword, keys.keys(), limit=1)
            keyword = keyword[0][0]
            try:
                if await self.config.user(member).get_raw(keyword):
                    await self.config.user(member).set_raw(keyword, value=False)
                    msg += f"Achievement {keyword} was successfully removed from {str(member)}.\n"
                elif not await self.config.user(member).get_raw(keyword):
                    await self.config.user(member).set_raw(keyword, value=True)
                    msg += f"Achievement {keyword} was successfully added to {str(member)}.\n"
            except Exception as e:
                return await ctx.send(embed=discord.Embed(color=discord.Colour.red(), description=f"**Something went wrong: {e}.**"))

        roles = await self.checkforroles(member)

        return await ctx.send(embed=discord.Embed(color=discord.Colour.green(), description="**" + msg + f"{roles}**"))

    async def checkforroles(self, member: discord.Member):
        msg = ""

        dt = member.guild.get_role(736956117518647356)
        if await self.config.user(member).pinch() and await self.config.user(member).dynamic():
            if dt not in member.roles:
                await member.add_roles(dt)
                msg += f"Double Trouble role added!\n"
        else:
            if dt in member.roles:
                await member.remove_roles(dt)
                msg += "Double Trouble role removed.\n"

        ss = member.guild.get_role(736960419922444348)
        if await self.config.user(member).trident() and await self.config.user(member).over() and await self.config.user(member).survivalist() and await self.config.user(member).after():
            if ss not in member.roles:
                await member.add_roles(ss)
                msg += f"Showdown Showoff role added!\n"
        else:
            if ss in member.roles:
                await member.remove_roles(ss)
                msg += "Showdown Showoff role removed.\n"

        gh = member.guild.get_role(736961181138419783)
        if await self.config.user(member).carrier() and await self.config.user(member).teamwork():
            if gh not in member.roles:
                await member.add_roles(gh)
                msg += f"Gem Hoarder role added!\n"
        else:
            if gh in member.roles:
                await member.remove_roles(gh)
                msg += "Gem Hoarder role removed.\n"

        sm = member.guild.get_role(736972276653883412)
        if await self.config.user(member).stale() and await self.config.user(member).op() and await self.config.user(member).clutch():
            if sm not in member.roles:
                await member.add_roles(sm)
                msg += f"Siege Machine role added!\n"
        else:
            if sm in member.roles:
                await member.remove_roles(sm)
                msg += "Siege Machine role removed.\n"

        bb = member.guild.get_role(736972900837490869)
        if await self.config.user(member).pro() and await self.config.user(member).turbo():
            if bb not in member.roles:
                await member.add_roles(bb)
                msg += f"Brawl Brace role added!\n"
        else:
            if bb in member.roles:
                await member.remove_roles(bb)
                msg += "Brawl Brace role removed.\n"

        hm = member.guild.get_role(736973167553151066)
        if await self.config.user(member).thief() and await self.config.user(member).close() and await self.config.user(member).guardian() and await self.config.user(member).deadlock():
            if hm not in member.roles:
                await member.add_roles(hm)
                msg += f"Heist Master role added!\n"
        else:
            if hm in member.roles:
                await member.remove_roles(hm)
                msg += "Heist Master role removed.\n"

        sc = member.guild.get_role(736973355512627200)
        if await self.config.user(member).assassin() and await self.config.user(member).bounty() and await self.config.user(member).massacre():
            if sc not in member.roles:
                await member.add_roles(sc)
                msg += f"Star Collector role added!\n"
        else:
            if sc in member.roles:
                await member.remove_roles(sc)
                msg += "Star Collector role removed.\n"

        hs = member.guild.get_role(736973807352283229)
        if await self.config.user(member).nailb() and await self.config.user(member).zoned() and await self.config.user(member).domination():
            if hs not in member.roles:
                await member.add_roles(hs)
                msg += f"Hot Shot role added!\n"
        else:
            if hs in member.roles:
                await member.remove_roles(hs)
                msg += "Hot Shot role removed.\n"

        ag = member.guild.get_role(736974837624471583)
        values = await self.config.user(member).all()
        result = True
        for v in values.values():
            if not v:
                result = False
        if result:
            await member.add_roles(ag)
            msg += f"Achievement God role added!\n"
        else:
            await member.remove_roles(ag)
            msg += "Achievement God role removed.\n"

        bl = member.guild.get_role(605758039928078338)
        if await self.config.user(member).brawll():
            if bl not in member.roles:
                await member.add_roles(bl)
                msg += f"Brawl Legend role added!\n"
        else:
            if bl in member.roles:
                await member.remove_roles(bl)
                msg += "Brawl Legend role removed.\n"

        lw = member.guild.get_role(736975188369080331)
        if await self.config.user(member).trophyg() and await self.config.user(member).triog() and await self.config.user(member).solog() and await self.config.user(member).duog() and await self.config.user(member).ppg() and await self.config.user(member).shut() and await self.config.user(member).robo() and await self.config.user(member).defender() and await self.config.user(member).city():
            if lw not in member.roles:
                await member.add_roles(lw)
                msg += f"Ladder Warrior role added!\n"
        else:
            if lw in member.roles:
                await member.remove_roles(lw)
                msg += "Ladder Warrior role removed.\n"

        return msg
