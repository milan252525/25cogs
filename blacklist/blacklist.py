import discord
from discord.ext import tasks

from redbot.core import commands, Config, checks

from bs.utils import badEmbed, goodEmbed, get_league_emoji, get_rank_emoji, get_brawler_emoji, remove_codes, calculate_starpoints

import asyncio
import brawlstats

class Blacklist(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=42424269)
        default_guild = {"blacklisted": {}}
        self.config.register_guild(**default_guild)
        self.bsconfig = Config.get_conf(None, identifier=5245652, cog_name="BrawlStarsCog")
        self.spainblacklistjob.start()

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
        self.spainblacklistjob.cancel()

    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def blacklisted(self, ctx):
        """View all blacklisted people"""
        await ctx.trigger_typing()
        
        if ctx.guild.id == 460550486257565697 and ctx.author.top_role < ctx.guild.get_role(462066723789471744):
            return await ctx.send("You can't use this command.")
        if ctx.guild.id != 460550486257565697 and not ctx.author.guild_permissions.kick_members or ctx.author.id != 359131399132807178:
            return await ctx.send("You can't use this command.")

        if len((await self.config.guild(ctx.guild).blacklisted()).keys()) < 1:
            return await ctx.send(
                embed=badEmbed(f"This server doesn't have anyone blacklisted!"))
        
        players = []
        keys = (await self.config.guild(ctx.guild).blacklisted()).keys()
        error = False
        for key in keys:
            try:
                player = await self.ofcbsapi.get_player(key)
                players.append(player)
                await asyncio.sleep(0.2)
            except brawlstats.errors.RequestError as e:
                error = True
        if error:
            await ctx.send(embed=badEmbed(f"BS API Error - some players aren't displayed!"))  

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
    @commands.has_permissions(administrator=True)
    @blacklisted.command(name="add")
    async def blacklist_add(self, ctx, tag: str, *, reason: str = ""):
        """
        Add a player to blacklist
        """
        await ctx.trigger_typing()

        if ctx.guild.id == 460550486257565697 and not ctx.author.guild_permissions.administrator:
            return await ctx.send("You can't use this command.")
        if ctx.guild.id != 460550486257565697 and not ctx.author.guild_permissions.kick_members:
            return await ctx.send("You can't use this command.")

        tag = tag.lower().replace('O', '0')
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
    @commands.has_permissions(administrator=True)
    @blacklisted.command(name="remove")
    async def blacklist_remove(self, ctx, tag: str):
        """
        Remove a person from blacklist
        """
        await ctx.trigger_typing()

        if ctx.guild.id == 460550486257565697 and not ctx.author.guild_permissions.administrator:
            return await ctx.send("You can't use this command.")
        if ctx.guild.id != 460550486257565697 and not ctx.author.guild_permissions.kick_members:
            return await ctx.send("You can't use this command.")

        tag = tag.lower().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        try:
            ign = await self.config.guild(ctx.guild).blacklisted.get_raw(tag, "ign")
            await self.config.guild(ctx.guild).blacklisted.clear_raw(tag)
            await ctx.send(embed=goodEmbed(f"{ign} was successfully removed from this server's blacklist!"))
        except KeyError:
            await ctx.send(embed=badEmbed(f"{ign} isn't blacklisted in this server!"))

    @tasks.loop(hours=4)
    async def spainblacklistjob(self):
        try:
            errors = 0
            ch = self.bot.get_channel(716329434466222092)
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
                        await ch.send(embed=discord.Embed(colour=discord.Colour.red(),
                                                                   description=f"Blacklisted user **{player.name}** with tag **{player.tag}** joined **{player.club.name}**!\nBlacklist reason: {reason}"))
        except Exception as e:
            await ch.send(e)

    @spainblacklistjob.before_loop
    async def before_spainblacklistjob(self):
        await asyncio.sleep(5)

    @commands.command()
    async def blacklistalert(self, ctx):
        midir = self.bot.get_user(359131399132807178)

        servers = await self.config.all_guilds()
        for server in servers:
            serverobj = self.bot.get_guild(server)
            servername = serverobj.name
            await midir.send(servername)
