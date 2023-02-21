import asyncio
import datetime
import textwrap
import traceback

import brawlstats
import discord
from bs.utils import badEmbed, goodEmbed
from discord.ext import tasks
from redbot.core import Config, checks, commands


class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=2536725)
        default_guild = {
            "roles": {
                "pres": None,
                "vp": None,
                "member": None,
                "bs": None,
                "guest": None,
                "leader": None,
                "leader_divider": None,  # for LA Asia
                "family": None,
                "remove": None,
                "otherclubs": None,
                "staff": None,
                "language": None,
                "memberclub": None,
                "senior": None,
                "autorole": False,
                "channel": None,
                "notifications": None,
                "ping": None,
                "pingchannel": None,
                "pingmessage": None,
                "invisible_roles": [],
                "lapres": None,
                "lavp": None
            }
        }
        self.config.register_guild(**default_guild)
        self.crconfig = Config.get_conf(
            None, identifier=2512325, cog_name="ClashRoyaleCog")
        self.bsconfig = Config.get_conf(
            None, identifier=5245652, cog_name="BrawlStarsCog")
        # self.sortroles.start()

    def cog_unload(self):
        self.sortroles.cancel()

    async def initialize(self):
        # crapikey = await self.bot.get_shared_api_tokens("crapi")
        # if crapikey["api_key"] is None:
        #     raise ValueError("The Clash Royale API key has not been set.")
        # self.crapi = clashroyale.OfficialAPI(crapikey["api_key"], is_async=True)

        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError(
                "The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.Client(
            ofcbsapikey["api_key"], is_async=True)

    def get_bs_config(self):
        if self.bsconfig is None:
            self.bsconfig = Config.get_conf(
                None, identifier=5245652, cog_name="BrawlStarsCog")
        return self.bsconfig

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.guild.id == 518276112040853515:
            verified = before.guild.get_role(753038839785848832)
            if verified not in before.roles and verified in after.roles:
                channel = self.bot.get_channel(518559373774028803)
                await channel.send(f"Welcome {after.mention} to Vanguard Gaming! This is the main channel for all your chatting needs. Make sure to grab some roles from <#750490004144390195>. Have fun!")

    async def removeroleifpresent(self, member: discord.Member, *roles):
        language = await self.config.guild(member.guild).roles.language()
        if member is None:
            if language == "en":
                return "Couldn't remove roles\n"
            elif language == "es":
                return "No logre dar los roles\n"
        msg = ""
        for role in roles:
            if role is None:
                continue
            if role in member.roles:
                await member.remove_roles(role)
                if language == "en":
                    msg += f"Removed **{str(role)}**\n"
                elif language == "es":
                    msg += f"Eliminado **{str(role)}**\n"
        return msg

    async def addroleifnotpresent(self, member: discord.Member, *roles):
        language = await self.config.guild(member.guild).roles.language()
        if member is None:
            if language == "en":
                return "Couldn't add roles\n"
            elif language == "es":
                return "No logre quitar los roles\n"
        msg = ""
        for role in roles:
            if role is None:
                continue
            if role not in member.roles:
                await member.add_roles(role)
                if language == "en":
                    msg += f"Added **{str(role)}**\n"
                elif language == "es":
                    msg += f"Añadido **{str(role)}**\n"
        return msg

    def get_badge(self, badge_id):
        guild = self.bot.get_guild(717766786019360769)
        guild2 = self.bot.get_guild(881132228858486824)
        em = discord.utils.get(guild.emojis, name=str(badge_id))
        if em is None:
            em = discord.utils.get(guild2.emojis, name=str(badge_id))
        return str(em)

    @commands.guild_only()
    # @commands.command(aliases=['nuevorol', 'vincular', 'salvar', 'nc'])
    async def newcomer(self, ctx, tag, member: discord.Member = None):
        staff = ctx.guild.get_role(await self.config.guild(ctx.guild).roles.staff())
        language = await self.config.guild(ctx.guild).roles.language()

        owners = (781512318760255488, 230947675837562880)

        if staff not in ctx.author.roles and not ctx.author.guild_permissions.kick_members and not ctx.author.guild_permissions.manage_messages and ctx.author.id not in owners and ctx.guild.id != 460550486257565697:
            if language == 'en':
                return await ctx.send("You can't use this command.")
            elif language == 'es':
                return await ctx.send("No puedes usar este comando.")

        await ctx.trigger_typing()

        roles_config = await self.config.guild(ctx.guild).roles()
        family = ctx.guild.get_role(roles_config['family'])
        guest = ctx.guild.get_role(roles_config['guest'])
        newcomer = ctx.guild.get_role(roles_config['remove'])
        brawlstars = ctx.guild.get_role(roles_config['bs'])
        vp = ctx.guild.get_role(roles_config['vp'])
        pres = ctx.guild.get_role(roles_config['pres'])
        otherclubs = ctx.guild.get_role(roles_config['otherclubs'])
        leader = ctx.guild.get_role(roles_config['leader'])
        leader_divider = ctx.guild.get_role(roles_config['leader_divider'])
        mmber = ctx.guild.get_role(roles_config['member'])
        memberclub = ctx.guild.get_role(roles_config['memberclub'])
        senior = ctx.guild.get_role(roles_config['senior'])
        notifications = ctx.guild.get_role(roles_config['notifications'])
        lapres = ctx.guild.get_role(roles_config['lapres'])
        lavp = ctx.guild.get_role(roles_config['lavp'])

        if member is not None and member != ctx.author:
            if newcomer in ctx.author.roles:
                return
        elif member is None:
            member = ctx.author

        tag = tag.lower().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        msg = ""
        try:
            player = await self.ofcbsapi.get_player(tag)
            player_in_club = "tag" in player.raw_data["club"]
            player_club = None

            await self.bsconfig.user(member).tag.set(tag.replace("#", ""))

            if player_in_club:
                try:
                    player_club = await self.ofcbsapi.get_club(player.club.tag)
                    badge = self.get_badge(player_club.raw_data['badgeId'])
                except brawlstats.errors.RequestError:
                    badge = "<:bsband:600741378497970177>"
            if language == 'en':
                cl_name = f"{badge} {player.club.name}" if "name" in player.raw_data[
                    "club"] else "<:noclub:661285120287834122> No club"
            elif language == 'es':
                cl_name = f"{badge} {player.club.name}" if "name" in player.raw_data[
                    "club"] else "<:noclub:661285120287834122> Sin club"
            msg += f"**{player.name}** <:bstrophy:552558722770141204> {player.trophies} {cl_name}\n"
        except brawlstats.errors.NotFoundError:
            if language == 'en':
                return await ctx.send(embed=badEmbed("No player with this tag found!"))
            elif language == 'es':
                return await ctx.send(embed=badEmbed("¡No se ha encontrado ningún jugador con este tag!"))

        except brawlstats.errors.RequestError as e:
            if language == 'en':
                return await ctx.send(embed=badEmbed(f"BS API is offline, please try again later! ({str(e)})"))
            elif language == 'es':
                return await ctx.send(embed=badEmbed(f"BS API está fuera de línea, por favor inténtalo de nuevo más tarde! ({str(e)})"))

        except Exception as e:
            if language == 'en':
                return await ctx.send("**Something went wrong, please send a personal message to our Modmail bot or try again!****")
            elif language == 'es':
                return await ctx.send("**¡Algo ha ido mal, por favor envía un mensaje personal al bot Modmail o inténtalo de nuevo!**")

        nick = f"{player.name}"
        try:
            await member.edit(nick=nick[:31])
            if language == 'en':
                msg += f"New nickname: **{nick[:31]}**\n"
            elif language == 'es':
                msg += f"Nuevo apodo: **{nick[:31]}**\n"
        except discord.Forbidden:
            if language == 'en':
                msg += f"I don't have permission to change nickname of this user!\n"
            elif language == 'es':
                msg += f"¡No tengo permisos para cambiar el apodo de este usuario!\n"
        except Exception as e:
            if language == 'en':
                return await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=f"Something went wrong: {str(e)}"))
            elif language == 'es':
                return await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=f"¡Algo ha ido mal: {str(e)}"))

        labs_guild = self.bot.get_guild(401883208511389716)
        labs_clubs = await self.bsconfig.guild(labs_guild).clubs()
        labs_tags_roles = {}
        for tag in labs_clubs:
            labs_tags_roles["#" + labs_clubs[tag]
                            ["tag"]] = labs_clubs[tag]["role"]

        local_tags_roles = {}
        local_clubs = await self.bsconfig.guild(ctx.guild).clubs()

        for tag in local_clubs:
            local_tags_roles["#" + local_clubs[tag]
                             ["tag"]] = local_clubs[tag]["role"]

        if player_in_club:
            member_role_expected = None
            if player.club.tag in local_tags_roles.keys():
                member_role_expected = ctx.guild.get_role(
                    local_tags_roles[player.club.tag])

            player_in_local_club = player.club.tag in local_tags_roles.keys()
            player_in_la_club = player.club.tag in labs_tags_roles.keys()

        msg += await self.removeroleifpresent(member, newcomer)
        msg += await self.addroleifnotpresent(member, notifications)

        if not player_in_club:
            msg += await self.addroleifnotpresent(member, guest, brawlstars)

        if player_in_club and not (player_in_la_club or player_in_local_club):
            msg += await self.addroleifnotpresent(member, guest, brawlstars)

        if player_in_club and player_in_la_club and not player_in_local_club:
            if player_club is not None:
                for mem in player_club.members:
                    if mem.tag == player.raw_data['tag']:
                        if mem.role.lower() == 'vicepresident':
                            msg += await self.addroleifnotpresent(member, lavp)
                        elif mem.role.lower() == 'president':
                            msg += await self.addroleifnotpresent(member, lapres)
                        break
            else:
                msg += "<:offline:642094554019004416> Couldn't retrieve player's club role. Try again later!"
            msg += await self.addroleifnotpresent(member, otherclubs, mmber, brawlstars)

        if player_in_club and player_in_local_club:
            if member_role_expected is None:
                msg += await self.addroleifnotpresent(member, guest, brawlstars)
                if language == 'en':
                    msg += f"Role for the club {player.club.name} not found.\n"
                elif language == 'es':
                    msg += f"No se ha encontrado un rol para el club {player.club.name}.\n"
                return await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))
            msg += await self.addroleifnotpresent(member, mmber, family, brawlstars, member_role_expected)

            if player_club is not None:
                for mem in player_club.members:
                    if mem.tag == player.raw_data['tag']:
                        if mem.role.lower() == 'vicepresident':
                            msg += await self.addroleifnotpresent(member, vp, leader, leader_divider)
                        elif mem.role.lower() == 'president':
                            msg += await self.addroleifnotpresent(member, pres, leader, leader_divider)
                        elif mem.role.lower() == 'senior':
                            msg += await self.addroleifnotpresent(member, senior)
                        elif mem.role.lower() == 'member':
                            msg += await self.addroleifnotpresent(member, memberclub)
                        break
            else:
                msg += "<:offline:642094554019004416> Couldn't retrieve player's club role. Try again later!"

        if msg != "":
            await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))

        if len(roles_config['invisible_roles']) > 0:
            for role_id in roles_config['invisible_roles']:
                await self.addroleifnotpresent(member, ctx.guild.get_role(role_id))

        if roles_config['ping']:
            pingch = self.bot.get_channel(roles_config['pingchannel'])
            message = roles_config['pingmessage']
            await pingch.send(member.mention + message)

    async def send_error(self, error, id):
        str_error = traceback.format_exception(
            type(error), error, error.__traceback__)

        wrapper = textwrap.TextWrapper(
            width=1000, max_lines=5, expand_tabs=False, replace_whitespace=False)
        messages = wrapper.wrap("".join(str_error))

        embed = discord.Embed(colour=discord.Color.red(), description=str(id))

        for i, m in enumerate(messages[:5], start=1):
            embed.add_field(
                name=f"Part {i}",
                value="```py\n" + m + "```",
                inline=False
            )

        error_channel = self.bot.get_channel(1077518660442263622)
        await error_channel.send(embed=embed)

    @tasks.loop(hours=4)
    async def sortroles(self):
        try:
            labs_guild = self.bot.get_guild(401883208511389716)
            labs_clubs = await self.bsconfig.guild(labs_guild).clubs()
            labs_tags_roles = {}
            for tag in labs_clubs:
                labs_tags_roles["#" + labs_clubs[tag]
                                ["tag"]] = labs_clubs[tag]["role"]

            for g in await self.config.all_guilds():
                guild = self.bot.get_guild(g)
                if guild is None:
                    continue
                if await self.config.guild(guild).roles.autorole():
                    roles_config = await self.config.guild(guild).roles()
                    language = roles_config['language']

                    ch = self.bot.get_channel(roles_config['channel'])
                    if ch is None:
                        continue
                    await ch.trigger_typing()

                    family = ch.guild.get_role(roles_config['family'])
                    guest = ch.guild.get_role(roles_config['guest'])
                    newcomer = ch.guild.get_role(roles_config['remove'])
                    brawlstars = ch.guild.get_role(roles_config['bs'])
                    vp = ch.guild.get_role(roles_config['vp'])
                    pres = ch.guild.get_role(roles_config['pres'])
                    otherclubs = ch.guild.get_role(roles_config['otherclubs'])
                    leader = ch.guild.get_role(roles_config['leader'])
                    leader_divider = ch.guild.get_role(
                        roles_config['leader_divider'])
                    mmber = ch.guild.get_role(roles_config['member'])
                    memberclub = ch.guild.get_role(roles_config['memberclub'])
                    senior = ch.guild.get_role(roles_config['senior'])
                    notifications = ch.guild.get_role(
                        roles_config['notifications'])
                    lapres = ch.guild.get_role(roles_config['lapres'])
                    lavp = ch.guild.get_role(roles_config['lavp'])
                    error_counter = 0

                    local_tags_roles = {}
                    local_clubs = await self.bsconfig.guild(ch.guild).clubs()

                    for tag in local_clubs:
                        local_tags_roles["#" + local_clubs[tag]
                                         ["tag"]] = local_clubs[tag]["role"]

                    for member in ch.guild.members:
                        if member is None or member.bot:
                            continue
                        tag = await self.bsconfig.user(member).tag()
                        if tag is None:
                            continue
                        # if tag is None and guild == 401883208511389716:
                        #     msg = ""
                        #     if pres in member.roles or vp in member.roles:
                        #         msg += "Has President or VP role, no tag saved.\n"
                        #         msg += await self.removeroleifpresent(member, vp, pres)
                        #         try:
                        #             await member.send(
                        #                 f"Hello {member.mention},\nyour (Vice)President role in LA Brawl Stars server has been removed.\nThe reason is you don't have your in-game tag saved at LA bot. You can fix it by saving your tag using `/save #YOURTAG`.\n")
                        #         except (discord.HTTPException, discord.Forbidden) as e:
                        #             msg += f"Couldn't send a DM with info. {str(e)}\n"
                        #         await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=msg, title=str(member),
                        #                                           timestamp=datetime.datetime.now()))
                        #     continue
                        try:
                            player = await self.ofcbsapi.get_player(tag)
                            await asyncio.sleep(0.3)
                        except brawlstats.errors.RequestError as e:
                            await ch.send(
                                embed=discord.Embed(colour=discord.Colour.red(), description=f"{str(member)} ({member.id}) #{tag}"))
                            error_counter += 1
                            if error_counter == 10:
                                await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=f"Stopping after 10 request errors! Displaying the last one:\n({str(e)})"))
                                break
                            await asyncio.sleep(1)
                            continue
                        except Exception as e:
                            return await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=f"**Something went wrong while requesting {tag}!**\n({str(e)})"))

                        msg = ""

                        msg += await self.addroleifnotpresent(member, notifications)

                        player_in_club = "tag" in player.raw_data["club"]

                        member_role_expected = None
                        if player_in_club and player.club.tag in local_tags_roles:
                            member_role_expected = ch.guild.get_role(
                                local_tags_roles[player.club.tag])

                        member_roles = []
                        for role in member.roles:
                            if role.id in local_tags_roles.values():
                                member_roles.append(role)

                        if len(member_roles) > 1:
                            msg += f"Found more than one club role. (**{', '.join([str(r) for r in member_roles])}**)\n"
                            for role in member_roles:
                                if role != member_role_expected:
                                    msg += await self.removeroleifpresent(member, role)

                        member_role = None if len(
                            member_roles) < 1 else member_roles[0]

                        player_in_local_club = player_in_club and player.club.tag in local_tags_roles.keys()
                        player_in_la_club = player_in_club and player.club.tag in labs_tags_roles.keys()

                        player_club = None
                        if player_in_club and (player_in_local_club or player_in_la_club):
                            try:
                                await asyncio.sleep(0.2)
                                player_club = await self.ofcbsapi.get_club(player.club.tag)
                            except brawlstats.errors.RequestError:
                                msg += "<:offline:642094554019004416> Couldn't retrieve player's club role."

                        if not player_in_club:
                            msg += await self.removeroleifpresent(member, family, vp, pres, newcomer, otherclubs, leader, leader_divider, mmber, memberclub, senior, member_role)
                            msg += await self.addroleifnotpresent(member, guest, brawlstars)

                        if player_in_club and not (player_in_la_club or player_in_local_club):
                            msg += await self.removeroleifpresent(member, family, vp, pres, newcomer, otherclubs, leader, leader_divider, mmber, memberclub, senior, member_role)
                            msg += await self.addroleifnotpresent(member, guest, brawlstars)

                        elif player_in_club and player_in_la_club and not player_in_local_club:
                            if player_club is not None:
                                for mem in player_club.members:
                                    if mem.tag == player.raw_data['tag']:
                                        if mem.role.lower() == 'vicepresident':
                                            msg += await self.removeroleifpresent(member, lapres)
                                            msg += await self.addroleifnotpresent(member, lavp)
                                        elif mem.role.lower() == 'president':
                                            msg += await self.removeroleifpresent(member, lavp)
                                            msg += await self.addroleifnotpresent(member, lapres)
                                        elif mem.role.lower() == 'senior':
                                            msg += await self.removeroleifpresent(member, lavp, lapres)
                                        elif mem.role.lower() == 'member':
                                            msg += await self.removeroleifpresent(member, lavp, lapres)
                                        break
                            msg += await self.removeroleifpresent(member, family, vp, pres, newcomer, leader, leader_divider, memberclub, senior, member_role, guest)
                            msg += await self.addroleifnotpresent(member, otherclubs, mmber, brawlstars)

                        elif player_in_club and player_in_local_club:
                            if member_role_expected is None:
                                msg += await self.removeroleifpresent(member, family, vp, pres, newcomer, otherclubs, leader, leader_divider, mmber, memberclub, senior, member_role)
                                msg += await self.addroleifnotpresent(member, guest, brawlstars)
                                if language == 'en':
                                    msg += f"Role for the club {player.club.name} is not saved.\n"
                                elif language == 'es':
                                    msg += f"El rol para el club {player.club.name} no está guardado.\n"
                                await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg, title=str(member), timestamp=datetime.datetime.now()))
                                continue
                            msg += await self.removeroleifpresent(member, newcomer, otherclubs, guest)
                            msg += await self.addroleifnotpresent(member, mmber, family, brawlstars)
                            if member_role is None:
                                msg += await self.addroleifnotpresent(member, member_role_expected)
                            elif member_role != member_role_expected:
                                msg += await self.removeroleifpresent(member, member_role)
                                msg += await self.addroleifnotpresent(member, member_role_expected)

                            if player_club is not None:
                                for mem in player_club.members:
                                    if mem.tag == player.raw_data['tag']:
                                        if mem.role.lower() == 'vicepresident':
                                            msg += await self.removeroleifpresent(member, pres, senior, memberclub)
                                            msg += await self.addroleifnotpresent(member, vp, leader, leader_divider)
                                        elif mem.role.lower() == 'president':
                                            msg += await self.removeroleifpresent(member, vp, senior, memberclub)
                                            msg += await self.addroleifnotpresent(member, pres, leader)
                                        elif mem.role.lower() == 'senior':
                                            msg += await self.removeroleifpresent(member, vp, pres, memberclub, leader, leader_divider)
                                            msg += await self.addroleifnotpresent(member, senior)
                                        elif mem.role.lower() == 'member':
                                            msg += await self.removeroleifpresent(member, vp, pres, senior, leader, leader_divider)
                                            msg += await self.addroleifnotpresent(member, memberclub)
                                        break

                        if msg != "":
                            await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg, title=str(member),
                                                              timestamp=datetime.datetime.now()))
                await asyncio.sleep(120)
        except Exception as e:
            await self.send_error(e, g)

    @sortroles.before_loop
    async def before_sortroles(self):
        await asyncio.sleep(10)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def setrole(self, ctx, key, role: discord.Role = None):
        await ctx.trigger_typing()
        key = key.lower()

        try:
            await self.config.guild(ctx.guild).roles.set_raw(key, value=role.id if role is not None else None)
            name = role.name if role is not None else "None"
            await ctx.send(embed=goodEmbed(f"Value {key} set to {name}."))
        except KeyError:
            await ctx.send(embed=badEmbed(f"{key.title()} isn't a valid keyword in this server."))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def setlang(self, ctx, lang):
        await ctx.trigger_typing()

        langs = ["en", "es"]

        if lang not in langs:
            return await ctx.send("No such language supported.")

        await self.config.guild(ctx.guild).roles.language.set(lang)
        await ctx.send(embed=goodEmbed(f"Value language set to {lang}."))

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def autorole(self, ctx, status: bool = True):
        await ctx.trigger_typing()

        await self.config.guild(ctx.guild).roles.autorole.set(status)
        await ctx.send(embed=goodEmbed(f"Value autorole set to {status}."))

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def autorolech(self, ctx, channel: int):
        await ctx.trigger_typing()

        try:
            ch = self.bot.get_channel(channel)
        except Exception as e:
            return await ctx.send(embed=badEmbed(f"Something went wrong: {e}."))

        await self.config.guild(ctx.guild).roles.channel.set(channel)
        name = ch.name if channel is not None else "None"
        await ctx.send(embed=goodEmbed(f"Autorole channel set to {name}."))

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def pingswitch(self, ctx, status: bool = True):
        await ctx.trigger_typing()

        await self.config.guild(ctx.guild).roles.ping.set(status)
        await ctx.send(embed=goodEmbed(f"Value ping set to {status}."))

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def pingch(self, ctx, channel: int):
        await ctx.trigger_typing()

        try:
            ch = self.bot.get_channel(channel)
        except Exception as e:
            return await ctx.send(embed=badEmbed(f"Something went wrong: {e}."))

        await self.config.guild(ctx.guild).roles.pingchannel.set(channel)
        name = ch.name if channel is not None else "None"
        await ctx.send(embed=goodEmbed(f"Ping channel set to {name}."))

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def pingmessage(self, ctx, *, message):
        await ctx.trigger_typing()

        await self.config.guild(ctx.guild).roles.pingmessage.set(message)
        await ctx.send(embed=goodEmbed(f"Value pingmessage set to {message}."))
