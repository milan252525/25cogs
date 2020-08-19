import discord

from redbot.core import commands, Config, checks
from bs.utils import goodEmbed, badEmbed

import asyncio
import brawlstats
from typing import Union
from fuzzywuzzy import process

class AchievementsSpain(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=18923497197)
        default_user = {"trabajo": False,
                        "carr": False,
                        "joy": False,
                        "astr": False,
                        "mas": False,
                        "caza": False,
                        "ast": False,
                        "calc": False,
                        "goleador": False,
                        "partida": False,
                        "ul": False,
                        "pro": False,
                        "ator": False,
                        "muer": False,
                        "destor": False,
                        "chata": False,
                        "into": False,
                        "alli": False,
                        "conj": False,
                        "lad": False,
                        "apa": False,
                        "tri": False,
                        "dina": False,
                        "hum": False,
                        "vict": False,
                        "duoe": False,
                        "huma": False,
                        "juga": False,
                        "estr": False,
                        "famo": False,
                        "maxe": False,
                        "braw": False,
                        "aho": False,
                        "empate": False,
                        "og": False,
                        "prob": False,
                        "derr": False,
                        "crack": False,
                        "vicia": False,
                        "novc": False,
                        "proc": False,
                        "diosc": False,
                        "novxp": False,
                        "proxp": False,
                        "diosxp": False,
                        "novr": False,
                        "pror": False,
                        "diosr": False,
                        "novtr": False,
                        "protr": False,
                        "diostr": False,
                        "novs": False,
                        "pros": False,
                        "dioss": False,
                        "novd": False,
                        "prod": False,
                        "diosd": False,
                        "destr": False,
                        "mata": False,
                        "ases": False,
                        "cazam": False,
                        "control": False,
                        "igua": False,
                        "por": False,
                        "domi": False}
        self.config.register_user(**default_user)

    async def initialize(self):
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.Client(ofcbsapikey["api_key"], is_async=True)

    @commands.command(aliases=['l'])
    async def logros(self, ctx, *, member: Union[discord.Member, str] = None):
        """Check yours or other person's achievements"""
        if ctx.guild.id != 460550486257565697:
            return await ctx.send(embed=badEmbed("No puedo usar esto aqui, lo siento."))

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
        if await self.config.user(member).trabajo():
            gg = gg + "Trabajo en equipo\n"
        if await self.config.user(member).carr():
            gg = gg + "Carrito\n"
        if await self.config.user(member).joy():
            gg = gg + "Joyería Exprés\n"
        if gg != "":
            aembed.add_field(name="Gem Grab", value=gg, inline=False)

        bounty = ""
        if await self.config.user(member).astr():
            bounty = bounty + "Astrónomo\n"
        if await self.config.user(member).mas():
            bounty = bounty + "Masacre\n"
        if await self.config.user(member).caza():
            bounty = bounty + "Caza Estrellas\n"
        if await self.config.user(member).ast():
            bounty = bounty + "Astronomía Básica\n"
        if await self.config.user(member).calc():
            bounty = bounty + "Calculado\n"
        if bounty != "":
            aembed.add_field(name="Bounty", value=bounty, inline=False)

        heist = ""
        if await self.config.user(member).into():
            heist = heist + "Intocable\n"
        if await self.config.user(member).alli():
            heist = heist + "Al Límite\n"
        if await self.config.user(member).conj():
            heist = heist + "Conjuro Espejo\n"
        if await self.config.user(member).lad():
            heist = heist + "Ladrón\n"
        if await self.config.user(member).apa():
            heist = heist + "A Palazos\n"
        if heist != "":
            aembed.add_field(name="Heist", value=heist, inline=False)

        bb = ""
        if await self.config.user(member).goleador():
            bb = bb + "Goleador Veloz\n"
        if await self.config.user(member).partida():
            bb = bb + "Partida Veloz\n"
        if await self.config.user(member).ul():
            bb = bb + "Último Empujón\n"
        if bb != "":
            aembed.add_field(name="Brawl Ball", value=bb, inline=False)

        siege = ""
        if await self.config.user(member).pro():
            siege = siege + "Protector\n"
        if await self.config.user(member).ator():
            siege = siege + "Atornillado\n"
        if await self.config.user(member).muer():
            siege = siege + "Muerte súbita\n"
        if await self.config.user(member).destor():
            siege = siege + "Destornillador Veloz\n"
        if await self.config.user(member).chata():
            siege = siege + "Chatarrero\n"
        if siege != "":
            aembed.add_field(name="Siege", value=siege, inline=False)

        hz = ""
        if await self.config.user(member).control():
            hz = hz + "Control Total\n"
        if await self.config.user(member).igua():
            hz = hz + "Igualados\n"
        if await self.config.user(member).por():
            hz = hz + "Por Los Pelos\n"
        if await self.config.user(member).domi():
            hz = hz + "Dominación\n"
        if hz != "":
            aembed.add_field(name="Hot Zone", value=hz, inline=False)

        ss = ""
        if await self.config.user(member).tri():
            ss = ss + "Tridente\n"
        if await self.config.user(member).dina():
            ss = ss + "Dinámico\n"
        if await self.config.user(member).hum():
            ss = ss + "Humildad\n"
        if await self.config.user(member).vict():
            ss = ss + "Victoria Invertida\n"
        if ss != "":
            aembed.add_field(name="Solo Showdown", value=ss, inline=False)

        ds = ""
        if await self.config.user(member).duoe():
            ds = ds + "Dúo estelar\n"
        if await self.config.user(member).huma():
            ds = ds + "Humildad a pares\n"
        if ds != "":
            aembed.add_field(name="Duo Showdown", value=ds, inline=False)

        events = ""
        if await self.config.user(member).destr():
            events = events + "Destructor de Robots\n"
        if await self.config.user(member).mata():
            events = events + "Mata Gigantes\n"
        if await self.config.user(member).ases():
            events = events + "Asesino\n"
        if await self.config.user(member).cazam():
            events = events + "Caza Monstruos\n"
        if events != "":
            aembed.add_field(name="Special Events", value=events, inline=False)

        misc = ""
        if await self.config.user(member).juga():
            misc = misc + "Jugador Vip\n"
        if await self.config.user(member).estr():
            misc = misc + "Estrella\n"
        if await self.config.user(member).famo():
            misc = misc + "Famoso\n"
        if await self.config.user(member).maxe():
            misc = misc + "Maxeado\n"
        if await self.config.user(member).braw():
            misc = misc + "Brawler Dios\n"
        if await self.config.user(member).aho():
            misc = misc + "Ahorrador\n"
        if await self.config.user(member).empate():
            misc = misc + "Empate Estelar\n"
        if await self.config.user(member).prob():
            misc = misc + "Pro Brawler\n"
        if await self.config.user(member).og():
            misc = misc + "OG\n"
        if await self.config.user(member).derr():
            misc = misc + "Derrota Estelar\n"
        if await self.config.user(member).crack():
            misc = misc + "Crack del push\n"
        if await self.config.user(member).vicia():
            misc = misc + "Viciado\n"
        if misc != "":
            aembed.add_field(name="Extras", value=misc, inline=False)

        exp = ""
        if await self.config.user(member).novxp():
            exp = exp + "Novato XP\n"
        elif await self.config.user(member).prop():
            exp = exp + "Pro XP\n"
        elif await self.config.user(member).diosxp():
            exp = exp + "Dios XP\n"
        if exp != "":
            aembed.add_field(name="Experience Levels", value=exp, inline=False)

        troph = ""
        if await self.config.user(member).novc():
            troph = troph + "Novato Copas\n"
        elif await self.config.user(member).proc():
            troph = troph + "Pro Copas\n"
        elif await self.config.user(member).diosc():
            troph = troph + "Dios Copas\n"
        if troph != "":
            aembed.add_field(name="Trophies", value=troph, inline=False)

        tvt = ""
        if await self.config.user(member).novtr():
            tvt = tvt + "Novato 3vs3\n"
        elif await self.config.user(member).protr():
            tvt = tvt + "Pro 3vs3\n"
        elif await self.config.user(member).diostr():
            tvt = tvt + "Dios 3vs3\n"
        if tvt != "":
            aembed.add_field(name="3v3 Wins", value=tvt, inline=False)

        solo = ""
        if await self.config.user(member).novs():
            solo = solo + "Novato Solo\n"
        elif await self.config.user(member).pros():
            solo = solo + "Pro Solo\n"
        elif await self.config.user(member).dios():
            solo = solo + "Dios Solo\n"
        if solo != "":
            aembed.add_field(name="Solo Showdown Wins", value=solo, inline=False)

        duo = ""
        if await self.config.user(member).novd():
            duo = duo + "Novato Dúo\n"
        elif await self.config.user(member).prod():
            duo = duo + "Pro Dúo\n"
        elif await self.config.user(member).diosd():
            duo = duo + "Dios Dúo\n"
        if duo != "":
            aembed.add_field(name="Duo Showdown Wins", value=duo, inline=False)

        pp = ""
        if await self.config.user(member).novr():
            pp = pp + "Novato Rankeds\n"
        elif await self.config.user(member).pror():
            pp = pp + "Pro Rankeds\n"
        elif await self.config.user(member).diosr():
            pp = pp + "Dios Rankeds\n"
        if pp != "":
            aembed.add_field(name="Power Play", value=pp, inline=False)

        return await ctx.send(embed=aembed)

    @commands.command(aliases=['al'])
    async def anadirlogros(self, ctx, member: discord.Member, *keywords):
        """Add or remove achievements from a person"""
        if ctx.guild.id != 460550486257565697 and ctx.channel.id != 745252036861493329:
            return await ctx.send(embed=discord.Embed(color=discord.Colour.red(), description="**No puedo usar esto aqui, lo siento**"))

        rolesna = ctx.guild.get_role(578685169930862596)
        if not ctx.author.guild_permissions.kick_members and rolesna not in ctx.author.roles:
            return await ctx.send(embed=discord.Embed(color=discord.Colour.red(), description="**No puedo usar esto, lo siento.**"))

        msg = ""
        for keyword in keywords:
            keys = await self.config.user(member).all()
            keyword = process.extract(keyword, keys.keys(), limit=1)
            keyword = keyword[0][0]
            try:
                if await self.config.user(member).get_raw(keyword):
                    await self.config.user(member).set_raw(keyword, value=False)
                    msg += f"-{keyword}\n"
                elif not await self.config.user(member).get_raw(keyword):
                    await self.config.user(member).set_raw(keyword, value=True)
                    msg += f"+{keyword}\n"
            except Exception as e:
                return await ctx.send(embed=discord.Embed(color=discord.Colour.red(), description=f"**Algo a ido mal: {e}.**"))

        roles = await self.checkforroles(member)

        return await ctx.send(embed=discord.Embed(title=f"{str(member)}", color=discord.Colour.green(), description=f"**{msg}{roles}**"))

    async def checkforroles(self, member: discord.Member):
        msg = ""

        dt = member.guild.get_role(704014954956849192)
        if await self.config.user(member).duoe() and await self.config.user(member).huma():
            if dt not in member.roles:
                await member.add_roles(dt)
                msg += f"Añadido Dúo estelar.\n"
        else:
            if dt in member.roles:
                await member.remove_roles(dt)
                msg += "Eliminado Dúo estelar.\n"

        ss = member.guild.get_role(745593615950282763)
        if await self.config.user(member).tri() and await self.config.user(member).dina() and await self.config.user(member).hum() and await self.config.user(member).vict():
            if ss not in member.roles:
                await member.add_roles(ss)
                msg += f"Añadido Último superviviente.\n"
        else:
            if ss in member.roles:
                await member.remove_roles(ss)
                msg += "Eliminado Último superviviente.\n"

        gh = member.guild.get_role(745592374637363220)
        if await self.config.user(member).carr() and await self.config.user(member).joy() and await self.config.user(member).trabajo():
            if gh not in member.roles:
                await member.add_roles(gh)
                msg += f"Añadido Minero Expléndido.\n"
        else:
            if gh in member.roles:
                await member.remove_roles(gh)
                msg += "Eliminado Minero Expléndido.\n"

        sm = member.guild.get_role(745593467446755350)
        if await self.config.user(member).pro() and await self.config.user(member).ator() and await self.config.user(member).muer() and await self.config.user(member).destor() and await self.config.user(member).chata():
            if sm not in member.roles:
                await member.add_roles(sm)
                msg += f"Añadido Mecánico.\n"
        else:
            if sm in member.roles:
                await member.remove_roles(sm)
                msg += "Eliminado Mecánico.\n"

        bb = member.guild.get_role(745592148103266365)
        if await self.config.user(member).goleador() and await self.config.user(member).partida() and await self.config.user(member).ul():
            if bb not in member.roles:
                await member.add_roles(bb)
                msg += f"Añadido Futbolista.\n"
        else:
            if bb in member.roles:
                await member.remove_roles(bb)
                msg += "Eliminado Futbolista.\n"

        hm = member.guild.get_role(745593106228838451)
        if await self.config.user(member).into() and await self.config.user(member).alli() and await self.config.user(member).conj() and await self.config.user(member).lad() and await self.config.user(member).apa():
            if hm not in member.roles:
                await member.add_roles(hm)
                msg += f"Añadido Atracador.\n"
        else:
            if hm in member.roles:
                await member.remove_roles(hm)
                msg += "Eliminado Atracador.\n"

        sc = member.guild.get_role(745593224856338432)
        if await self.config.user(member).astr() and await self.config.user(member).mas() and await self.config.user(member).caza() and await self.config.user(member).ast() and await self.config.user(member).calc():
            if sc not in member.roles:
                await member.add_roles(sc)
                msg += f"Añadido Cazador Experto.\n"
        else:
            if sc in member.roles:
                await member.remove_roles(sc)
                msg += "Eliminado Cazador Experto.\n"

        hs = member.guild.get_role(745593528754896946)
        if await self.config.user(member).control() and await self.config.user(member).igua() and await self.config.user(member).por() and await self.config.user(member).domi():
            if hs not in member.roles:
                await member.add_roles(hs)
                msg += f"Añadido Conquistador.\n"
        else:
            if hs in member.roles:
                await member.remove_roles(hs)
                msg += "Eliminado Conquistador.\n"

        ag = member.guild.get_role(745594510989459456)
        values = await self.config.user(member).all()
        result = True
        for v in values:
            if v == "novc" or v == "proc" or v == "novxp" or v == "proxp" or v == "novtr" or v == "protr" or v == "novs" or v == "pros" or v == "novd" or v == "prod" or v == "novr" or v == "pror":
                continue
            if not await self.config.user(member).get_raw(v):
                result = False
        if result and ag not in member.roles:
            await member.add_roles(ag)
            msg += f"Añadido Dios de los desafíos.\n"
        elif not result and ag in member.roles:
            await member.remove_roles(ag)
            msg += "Eliminado Dios de los desafíos.\n"

        bl = member.guild.get_role(714898755220144181)
        if await self.config.user(member).crack():
            if bl not in member.roles:
                await member.add_roles(bl)
                msg += f"Añadido Crack del push.\n"
        else:
            if bl in member.roles:
                await member.remove_roles(bl)
                msg += "Eliminado Crack del push.\n"

        lw = member.guild.get_role(745594560582909952)
        if await self.config.user(member).diosc() and await self.config.user(member).diostr() and await self.config.user(member).dioss() and await self.config.user(member).diosd() and await self.config.user(member).diosr() and await self.config.user(member).destr() and await self.config.user(member).mata() and await self.config.user(member).ases() and await self.config.user(member).cazam():
            if lw not in member.roles:
                await member.add_roles(lw)
                msg += f"Añadido Ladder Warrior.\n"
        else:
            if lw in member.roles:
                await member.remove_roles(lw)
                msg += "Eliminado Ladder Warrior.\n"

        return msg
