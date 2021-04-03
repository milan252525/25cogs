import discord
from discord.ext import tasks
from redbot.core import commands, Config, checks

from bs.utils import badEmbed, goodEmbed

from re import sub
import asyncio
import brawlstats

class Blacklist(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=42424269)
        default_guild = {"blacklisted": {}}
        self.config.register_guild(**default_guild)
        self.bsconfig = Config.get_conf(None, identifier=5245652, cog_name="BrawlStarsCog")
        self.spainstaffbl.start()
        self.blacklistalert.start()
        self.deruculablacklistjob.start()

    async def initialize(self):
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.Client(ofcbsapikey["api_key"], is_async=True)

    def get_bs_config(self):
        if self.bsconfig is None:
            self.bsconfig = Config.get_conf(None, identifier=5245652, cog_name="BrawlStarsCog")
        return self.bsconfig
        
    def cog_unload(self):
        self.spainstaffbl.cancel()
        self.blacklistalert.cancel()
        self.deruculablacklistjob.cancel()

    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def blacklisted(self, ctx):
        """View all blacklisted people"""
        await ctx.trigger_typing()
        
        if ctx.guild.id == 724202847822151680 and ctx.author.top_role < ctx.guild.get_role(822458522322599956):
            return await ctx.send("You can't use this command.")
        if ctx.guild.id != 724202847822151680 and not ctx.author.guild_permissions.kick_members:
            return await ctx.send("You can't use this command.")

        if len((await self.config.guild(ctx.guild).blacklisted()).keys()) < 1:
            return await ctx.send(
                embed=badEmbed(f"This server doesn't have anyone blacklisted!"))
        
        players = []
        keys = (await self.config.guild(ctx.guild).blacklisted()).keys()
        errored = ""
        for key in keys:
            try:
                player = await self.ofcbsapi.get_player(key.replace("o", "0"))
                players.append(player)
                await asyncio.sleep(0.04)
            except brawlstats.errors.RequestError:
                errored += f"{key}\n"
        if errored != "":
            await ctx.send(embed=badEmbed(f"BS API Error - some players aren't displayed!\nErrors in following tags:\n{errored}"))  

        msg = ""
        alertembed = False
        messages = []
        for plr in players:
            alert = False
            key = ""
            clubname = ""
            for k in (await self.config.guild(ctx.guild).blacklisted()).keys():
                if plr.tag.replace("#", "").lower() == k:
                    key = k

            player_in_club = "name" in plr.raw_data["club"]
            if player_in_club:
                clubname = plr.club.name
            else:
                clubname = "No club"

            await self.config.guild(ctx.guild).blacklisted.set_raw(key, 'ign', value=plr.name)
            await self.config.guild(ctx.guild).blacklisted.set_raw(key, 'club', value=clubname)

            clubs = []
            for keey in (await self.get_bs_config().guild(ctx.guild).clubs()).keys():
                club = await self.get_bs_config().guild(ctx.guild).clubs.get_raw(keey, "tag")
                clubs.append(club)

            if player_in_club:
                if plr.club.tag.strip("#") in clubs:
                    alert = True
                    alertembed = True

            keyforembed = "#" + key.upper()

            if len(msg) > 1800:
                messages.append(msg)
                msg = ""

            reason = await self.config.guild(ctx.guild).blacklisted.get_raw(key, "reason", default="")
            if alert:
                msg += f"--->{plr.name}({keyforembed}) <:bsband:600741378497970177> **{clubname}** Reason: {reason}<---\n"
            if not alert:
                msg += f"{plr.name}({keyforembed}) <:bsband:600741378497970177> **{clubname}** Reason: {reason}\n"

        if len(msg) > 0:
            messages.append(msg)

        for m in messages:
            if m == m[0]:
                if alertembed:
                    await ctx.send(embed=discord.Embed(color=discord.Colour.red(), description=m, title="Blacklist"))
                elif not alertembed:
                    await ctx.send(embed=discord.Embed(color=discord.Colour.green(), description=m, title="Blacklist"))
            else:
                if alertembed:
                    await ctx.send(embed=discord.Embed(color=discord.Colour.red(), description=m))
                elif not alertembed:
                    await ctx.send(embed=discord.Embed(color=discord.Colour.green(), description=m))

    @commands.guild_only()
    @blacklisted.command(name="add")
    async def blacklist_add(self, ctx, tag: str, *, reason: str = ""):
        """
        Add a player to blacklist
        """
        await ctx.trigger_typing()

        if ctx.guild.id == 724202847822151680 and not ctx.author.guild_permissions.administrator:
            return await ctx.send("You can't use this command.")
        if ctx.guild.id != 724202847822151680 and not ctx.author.guild_permissions.kick_members:
            return await ctx.send("You can't use this command.")

        tag = tag.lower().replace('o', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        if tag in (await self.config.guild(ctx.guild).blacklisted()).keys():
            return await ctx.send(embed=badEmbed("This person is already blacklisted!"))

        try:
            player = await self.ofcbsapi.get_player(tag)
            player_in_club = "name" in player.raw_data["club"]
            if player_in_club:
                clubname = player.club.name
            else:
                clubname = "No club"
            result = {
                "ign": player.name,
                "club": clubname,
                "reason": reason
            }
            await self.config.guild(ctx.guild).blacklisted.set_raw(tag, value=result)
            await ctx.send(embed=goodEmbed(f"{player.name} was successfully blacklisted!"))

        except brawlstats.errors.NotFoundError as e:
            return await ctx.send(embed=badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send(
                f"**Something went wrong, please send a personal message to LA Modmail bot or try again!** ({e})")

    @commands.guild_only()
    @blacklisted.command(name="remove")
    async def blacklist_remove(self, ctx, tag: str):
        """
        Remove a person from blacklist
        """
        await ctx.trigger_typing()

        if ctx.guild.id == 724202847822151680 and not ctx.author.guild_permissions.administrator:
            return await ctx.send("You can't use this command.")
        if ctx.guild.id != 724202847822151680 and not ctx.author.guild_permissions.kick_members:
            return await ctx.send("You can't use this command.")

        tag = tag.lower().replace('o', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        try:
            ign = await self.config.guild(ctx.guild).blacklisted.get_raw(tag, "ign")
            await self.config.guild(ctx.guild).blacklisted.clear_raw(tag)
            await ctx.send(embed=goodEmbed(f"{ign} was successfully removed from this server's blacklist!"))
        except KeyError:
            await ctx.send(embed=badEmbed(f"#{tag} isn't blacklisted in this server!"))

    @blacklisted.command(name="check")
    async def blacklist_check(self, ctx, tag: str):
        """
        Check whether a person is blacklisted
        """
        await ctx.trigger_typing()

        if ctx.guild.id == 724202847822151680 and ctx.author.top_role < ctx.guild.get_role(822458522322599956):
            return await ctx.send("You can't use this command.")
        if ctx.guild.id != 724202847822151680 and not ctx.author.guild_permissions.kick_members:
            return await ctx.send("You can't use this command.")

        tag = tag.lower().replace('o', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        blacklisted = False
        guild = ""
        name = ""
        servers = await self.config.all_guilds()
        for server in servers:
            serverobj = self.bot.get_guild(server)
            if serverobj is not None:
                try:
                    name = await self.config.guild(serverobj).blacklisted.get_raw(tag, "ign")
                    guild = serverobj.name
                    blacklisted = True
                except KeyError:
                    continue

        if blacklisted:
            await ctx.send(embed=goodEmbed(f"{name} is indeed blacklisted on {guild}!"))
        else:
            await ctx.send(embed=badEmbed(f"Looks like this tag isn't blacklisted anywhere!"))
        
    @tasks.loop(hours=4)
    async def spainstaffbl(self):
        try:
            errors = 0
            ch = self.bot.get_channel(822859587790569493)
            await ch.trigger_typing()
            clubs = []
            saved_clubs = await self.bsconfig.guild(ch.guild).clubs()
            for key in saved_clubs.keys():
                club = saved_clubs[key]["tag"]
                clubs.append(club)

            blacklisted = await self.config.guild(ch.guild).blacklisted()
            for tag in blacklisted.keys():
                try:
                    player = await self.ofcbsapi.get_player(tag)
                    player_in_club = "name" in player.raw_data["club"]
                    await asyncio.sleep(1)
                except brawlstats.errors.RequestError as e:
                    await asyncio.sleep(5)
                    errors += 1
                    if errors == 20:
                        break
                except Exception as e:
                    return await ch.send(embed=discord.Embed(colour=discord.Colour.red(),
                                                             description=f"**Algo ha ido mal solicitando {tag}!**\n({str(e)})"))

                if player_in_club:
                    if player.club.tag.strip("#") in clubs:
                        roletoping = None
                        for key in saved_clubs:
                            if saved_clubs[key]['tag'] == player.club.tag.upper().replace("#", ""):
                                roletoping = ch.guild.get_role(saved_clubs[key]['role']) if 'role' in saved_clubs[key] else None
                                break
                        if roletoping is None:
                            party = f"No se ha encontrado un rol para el club {player.club.name}"
                        else:
                            party = roletoping.mention
                        reason = await self.config.guild(ch.guild).blacklisted.get_raw(tag, "reason", default="")
                        await ch.send(content=f"Club responsable: {party}", embed=discord.Embed(colour=discord.Colour.red(),
                                                                   description=f"Miembro de la blacklist **{player.name}** con el tag **{player.tag}** se ha unido a **{player.club.name}**!\nCon motivo de blacklist: {reason}"))
        except Exception as e:
            await ch.send(e)
            
    @spainstaffbl.before_loop
    async def before_spainstaffbl(self):
        await asyncio.sleep(60*30)

    @tasks.loop(hours=8)
    async def blacklistalert(self):
        try:
            ch = self.bot.get_channel(726824198663700540)
            errors = 0
            await ch.trigger_typing()
            clubs = []
            saved_clubs = await self.bsconfig.guild(ch.guild).clubs()
            for key in saved_clubs.keys():
                club = saved_clubs[key]["tag"]
                clubs.append(club)

            servers = await self.config.all_guilds()
            for server in servers:
                serverobj = self.bot.get_guild(server)
                if serverobj is not None:
                    tags = await self.config.guild(serverobj).blacklisted()
                    errored = ""
                    for tag in tags:
                        try:
                            player = await self.ofcbsapi.get_player(tag)
                            player_in_club = "name" in player.raw_data["club"]
                            await asyncio.sleep(1)
                        except brawlstats.errors.RequestError as e:
                            await asyncio.sleep(5)
                            errored += f"{tag}\n"
                            errors += 1
                            if errors == 30:
                                await ch.send(embed=discord.Embed(description=errored, title=f"ERRORS - {serverobj.name}"))
                                break
                        except Exception as e:
                            return await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=f"**Something went wrong while requesting {tag}!**\n({str(e)})"))

                        if player_in_club:
                            if player.club.tag.strip("#") in clubs:
                                roletoping = None
                                for key in saved_clubs:
                                    if saved_clubs[key]['tag'] == player.club.tag.upper().replace("#", ""):
                                        roletoping = ch.guild.get_role(saved_clubs[key]['role']) if 'role' in saved_clubs[key] else None
                                        break
                                if roletoping is None:
                                    party = f"Couldn't find a role for the club {player.club.name}"
                                else:
                                    party = roletoping.mention
                                reason = await self.config.guild(serverobj).blacklisted.get_raw(tag, "reason", default="")
                                await ch.send(content=f"Source: {serverobj.name}\nResponsible party: {party}", embed=discord.Embed(colour=discord.Colour.red(),
                                                                  description=f"Blacklisted user **{player.name}** with tag **{player.tag}** joined **{player.club.name}**!\nBlacklist reason: {reason}"))
                    if errored != "":
                        await ch.send(embed=discord.Embed(description=errored, title=f"ERRORS - {serverobj.name}"))
        except Exception as e:
            await ch.send(e)

    @blacklistalert.before_loop
    async def before_blacklistalert(self):
        await asyncio.sleep(60*20)

    @tasks.loop(hours=8)
    async def deruculablacklistjob(self):
        try:
            errors = 0
            ch = self.bot.get_channel(825199968419053596)
            await ch.trigger_typing()
            clubs = []
            saved_clubs = await self.bsconfig.guild(ch.guild).clubs()
            for key in saved_clubs.keys():
                club = saved_clubs[key]["tag"]
                clubs.append(club)

            blacklisted = await self.config.guild(ch.guild).blacklisted()
            for tag in blacklisted.keys():
                try:
                    player = await self.ofcbsapi.get_player(tag)
                    player_in_club = "name" in player.raw_data["club"]
                    await asyncio.sleep(1)
                except brawlstats.errors.RequestError as e:
                    await asyncio.sleep(5)
                    errors += 1
                    if errors == 30:
                        break
                except Exception as e:
                    return await ch.send(embed=discord.Embed(colour=discord.Colour.red(),
                                                             description=f"**Algo ha ido mal solicitando {tag}!**\n({str(e)})"))

                if player_in_club:
                    if player.club.tag.strip("#") in clubs:
                        reason = await self.config.guild(ch.guild).blacklisted.get_raw(tag, "reason", default="")
                        await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=f"Miembro de la blacklist **{player.name}** con el tag **{player.tag}** se ha unido a **{player.club.name}**!\nCon motivo de blacklist: {reason}"))
        except Exception as e:
            await ch.send(e)

    @deruculablacklistjob.before_loop
    async def before_deruculablacklistjob(self):
        await asyncio.sleep(60*50)


