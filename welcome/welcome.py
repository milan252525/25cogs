import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.chat_formatting import pagify
from bs.utils import goodEmbed, badEmbed
from discord.ext import tasks
from random import choice
from re import sub
import traceback
import textwrap 

import datetime
import clashroyale
import brawlstats
import asyncio
import time

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
                "guest" : None, 
                "leader": None,
                "leader_divider": None, #for LA Asia
                "family" : None, 
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
        self.crconfig = Config.get_conf(None, identifier=2512325, cog_name="ClashRoyaleCog")
        self.bsconfig = Config.get_conf(None, identifier=5245652, cog_name="BrawlStarsCog")
        self.sortroles.start()
        self.mainsortroles.start()
        #self.sortrolesevents.start()

    def cog_unload(self):
        self.sortroles.cancel()
        self.mainsortroles.cancel()
        #self.sortrolesevents.cancel()

    async def initialize(self):
        crapikey = await self.bot.get_shared_api_tokens("crapi")
        if crapikey["api_key"] is None:
            raise ValueError("The Clash Royale API key has not been set.")
        self.crapi = clashroyale.OfficialAPI(crapikey["api_key"], is_async=True)
        
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.Client(ofcbsapikey["api_key"], is_async=True)

    def get_bs_config(self):
        if self.bsconfig is None:
            self.bsconfig = Config.get_conf(None, identifier=5245652, cog_name="BrawlStarsCog")
        return self.bsconfig
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        #if member.guild.id == 440960893916807188 and not member.bot:
        #    await self.do_setup(member)
        #if member.guild.id == 593248015729295360 and not member.bot:
            #await self.do_setup_LAFC(member)
        #if member.guild.id == 654334199494606848 and not member.bot:
            #await self.do_setup_LABSevent(member)
        if member.guild.id == 704457125295947887 and not member.bot: #LA NA unverified autorole
            await member.add_roles(member.guild.get_role(785243512199184395))
        if member.guild.id == 585075868188278784 and not member.bot: #LA Asia unverified autorole
            await member.add_roles(member.guild.get_role(795641413126586408))

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.guild.id == 401883208511389716:
            if before.pending != after.pending:
                guest_role = before.guild.get_role(578260960981286923)
                channel = self.bot.get_channel(405159360222986253)
                await after.add_roles(guest_role)
                await channel.send(f"Welcome {after.mention} to LA Gaming! Be sure to check out our <#582211768814927882> and <#582211785189359646> and send a picture of your profile in <#555662656736985090> if you play Brawl Stars. Enjoy!")

    #DISABLED
    async def do_setup(self, member):
        welcome = self.bot.get_channel(674348799673499671)
        welcomeEmbed = discord.Embed(colour=discord.Colour.blue())
        welcomeEmbed.set_image(url="https://i.imgur.com/wwhgP4f.png")
        text = f"Welcome to **LA** {member.mention}!\nMake sure to read <#713858515135103047> and <#713882338018459729> to familiarise yourself with the server.\nPlease type **/setup cr #your\\_cr\\_tag** or **/setup bs #your\\_bs\\_tag**,\nfor other games type **/setup other** to get verified and see rest of the server!"
        await welcome.send(embed=welcomeEmbed)
        await welcome.send(text)

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

    @commands.command(aliases=['nuevorol', 'vincular', 'salvar', 'nc'])
    @commands.guild_only()
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
                cl_name = f"{badge} {player.club.name}" if "name" in player.raw_data["club"] else "<:noclub:661285120287834122> No club"
            elif language == 'es':
                cl_name = f"{badge} {player.club.name}" if "name" in player.raw_data["club"] else "<:noclub:661285120287834122> Sin club"
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
                return await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!****")
            elif language == 'es':
                return await ctx.send("**¡Algo ha ido mal, por favor envía un mensaje personal al bot LA Modmail o inténtalo de nuevo!**")

        nick = f"{player.name}"
        try:
            await member.edit(nick=nick[:31])
            if language == 'en':
                msg += f"New nickname: **{nick[:31]}**\n"
            elif language == 'es':
                msg += f"Nuevo apodo: **{nick[:31]}**\n"
        except discord.Forbidden:
            if language == 'en':
                msg += f"I dont have permission to change nickname of this user!\n"
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
            labs_tags_roles["#" + labs_clubs[tag]["tag"]] = labs_clubs[tag]["role"]

        local_tags_roles = {}
        local_clubs = await self.bsconfig.guild(ctx.guild).clubs()

        for tag in local_clubs:
            local_tags_roles["#" + local_clubs[tag]["tag"]] = local_clubs[tag]["role"]

        if player_in_club:
            member_role_expected = None
            if player.club.tag in local_tags_roles.keys():
                member_role_expected = ctx.guild.get_role(local_tags_roles[player.club.tag])

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
        str_error = traceback.format_exception(type(error), error, error.__traceback__)

        wrapper = textwrap.TextWrapper(width=1000, max_lines=5, expand_tabs=False, replace_whitespace=False)
        messages = wrapper.wrap("".join(str_error))

        embed = discord.Embed(colour=discord.Color.red(), description=str(id))

        for i, m in enumerate(messages[:5], start=1):
            embed.add_field(
                name=f"Part {i}",
                value="```py\n" + m + "```",
                inline=False
            )
            
        error_channel = self.bot.get_channel(722486276288282744)
        await error_channel.send(embed=embed)

    @tasks.loop(hours=4)
    async def sortroles(self):
        try:
            labs_guild = self.bot.get_guild(401883208511389716)
            labs_clubs = await self.bsconfig.guild(labs_guild).clubs()
            labs_tags_roles = {}
            for tag in labs_clubs:
                labs_tags_roles["#" + labs_clubs[tag]["tag"]] = labs_clubs[tag]["role"]

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
                    leader_divider = ch.guild.get_role(roles_config['leader_divider'])
                    mmber = ch.guild.get_role(roles_config['member'])
                    memberclub = ch.guild.get_role(roles_config['memberclub'])
                    senior = ch.guild.get_role(roles_config['senior'])
                    notifications = ch.guild.get_role(roles_config['notifications'])
                    lapres = ch.guild.get_role(roles_config['lapres'])
                    lavp = ch.guild.get_role(roles_config['lavp'])
                    error_counter = 0

                    local_tags_roles = {}
                    local_clubs = await self.bsconfig.guild(ch.guild).clubs()

                    for tag in local_clubs:
                        local_tags_roles["#" + local_clubs[tag]["tag"]] = local_clubs[tag]["role"]

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
                            member_role_expected = ch.guild.get_role(local_tags_roles[player.club.tag])
                        
                        member_roles = []
                        for role in member.roles:
                            if role.id in local_tags_roles.values():
                                member_roles.append(role)

                        if len(member_roles) > 1:
                            msg += f"Found more than one club role. (**{', '.join([str(r) for r in member_roles])}**)\n"
                            for role in member_roles:
                                if role != member_role_expected:
                                    msg += await self.removeroleifpresent(member, role)

                        member_role = None if len(member_roles) < 1 else member_roles[0]

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

    @tasks.loop(hours=4)
    async def mainsortroles(self):
        try:
            ch = self.bot.get_channel(756486248675147776)
            await ch.trigger_typing()
            newcomer = ch.guild.get_role(597767307397169173)
            roleVerifiedMember = ch.guild.get_role(597768235324145666)
            roleBSMember = ch.guild.get_role(514642403278192652)
            roleCRMember = ch.guild.get_role(475043204861788171)
            roleCR = ch.guild.get_role(523444129221312522)
            roleBS = ch.guild.get_role(523444501096824947)
            roleGuest = ch.guild.get_role(472632693461614593)

            for member in ch.guild.members:
                if member.bot:
                    continue
                bstag = await self.bsconfig.user(member).tag()
                crtag = await self.crconfig.user(member).tag()
                if crtag is None and bstag is None:
                    continue
                try:
                    bsplayer = None
                    crplayer = None
                    if bstag is not None:
                        bsplayer = await self.ofcbsapi.get_player(bstag)
                    if crtag is not None:
                        crplayer = await self.crapi.get_player(crtag)
                    await asyncio.sleep(0.3)
                except brawlstats.errors.RequestError as e:
                    await ch.send(embed=discord.Embed(colour=discord.Colour.red(),
                                                      description=f"BS: {str(member)} ({member.id}) #{bstag}"))
                    continue
                except clashroyale.RequestError as e:
                    await ch.send(embed=discord.Embed(colour=discord.Colour.red(),
                                                      description=f"CR: {str(member)} ({member.id}) #{crtag}"))
                    continue
                except Exception as e:
                    return await ch.send(embed=discord.Embed(colour=discord.Colour.red(),
                                                             description=f"**Something went wrong while requesting BS:{bstag}, CR:{crtag}!**\n({str(e)})"))

                msg = ""
                bstags = []
                if bsplayer is not None:
                    player_in_club = "name" in bsplayer.raw_data["club"]
                    if player_in_club:
                        labs = self.bot.get_guild(401883208511389716)
                        officialclubs = await self.bsconfig.guild(labs).clubs()
                        for ofkey in officialclubs.keys():
                            bstags.append("#" + officialclubs[ofkey]["tag"])
                crtags = []
                if crplayer is not None:
                    if crplayer.clan is not None:
                        clubs = await self.crconfig.guild(ch.guild).clans()
                        for key in clubs.keys():
                            crtags.append(clubs[key]["tag"])

                if bsplayer is not None and crplayer is not None:
                    if not player_in_club and crplayer.clan is None:
                        msg += await self.removeroleifpresent(member, roleBSMember, roleCRMember, roleCR, roleBS, newcomer)
                        msg += await self.addroleifnotpresent(member, roleGuest, roleVerifiedMember)
                        if msg != "":
                            await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg, title=str(member),
                                                              timestamp=datetime.datetime.now()))
                            continue

                if bsplayer is not None:
                    if player_in_club and bsplayer.club.tag not in bstags:
                        msg += await self.removeroleifpresent(member, roleBSMember, roleGuest, newcomer)
                        msg += await self.addroleifnotpresent(member, roleBS, roleVerifiedMember)
                    elif player_in_club and bsplayer.club.tag in bstags:
                        msg += await self.removeroleifpresent(member, roleGuest, newcomer)
                        msg += await self.addroleifnotpresent(member, roleBS, roleVerifiedMember, roleBSMember)

                if crplayer is not None:
                    if crplayer.clan is not None and crplayer.clan.tag.replace("#", "") not in crtags:
                        msg += await self.removeroleifpresent(member, roleCRMember, roleGuest, newcomer)
                        msg += await self.addroleifnotpresent(member, roleCR, roleVerifiedMember)
                    elif crplayer.clan is not None and crplayer.clan.tag in crtags:
                        msg += await self.removeroleifpresent(member, roleGuest, newcomer)
                        msg += await self.addroleifnotpresent(member, roleCR, roleVerifiedMember, roleCRMember)


                if msg != "":
                    await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg, title=str(member), timestamp=datetime.datetime.now()))
        except Exception as e:
            await ch.send(traceback.format_exc())

    @mainsortroles.before_loop
    async def before_mainsortroles(self):
        await asyncio.sleep(150)

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

    #DISABLED
    #@commands.command()
    #@commands.guild_only()
    async def setup(self, ctx, game, tag = "", member: discord.Member = None):
        if ctx.channel.id != 674348799673499671:
            return await ctx.send(embed=discord.Embed(description="This command can't be used in this channel.", colour=discord.Colour.red()))
        if member == None:
            member = ctx.author

        if not (game == "cr" or game == "bs" or game == "other"):
            return await ctx.send(embed=discord.Embed(description="That's not a valid option (`cr`, `bs` or `other`)!", colour=discord.Colour.red()))

        if (game == "cr" or game == "bs") and (tag == "" or len(tag) < 3):
            return await ctx.send(embed=discord.Embed(description="That doesn't look like a valid tag!", colour=discord.Colour.red()))

        globalChat = self.bot.get_channel(556425378764423179)
        newcomer = member.guild.get_role(597767307397169173)
        roleVerifiedMember = member.guild.get_role(597768235324145666)
        roleBSMember = member.guild.get_role(514642403278192652)
        roleCRMember = member.guild.get_role(475043204861788171)
        roleCR = member.guild.get_role(523444129221312522)
        roleBS = member.guild.get_role(523444501096824947)
        roleGuest = member.guild.get_role(472632693461614593)

        msg = ""
        if game.lower() == "bs":
            tag = tag.lower().replace('O', '0')
            if tag.startswith("#"):
                tag = tag.strip('#')
            try:
                player = await self.ofcbsapi.get_player(tag)
                nick = f"{player.name} | {player.club.name}" if "name" in player.raw_data["club"] else f"{player.name}"
                try:
                    await member.edit(nick=nick[:31])
                    msg += f"Nickname changed: {nick[:31]}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change nickname of this user. ({nick[:31]})\n"

                await self.get_bs_config().user(member).tag.set(tag)

                try:
                    await member.add_roles(roleVerifiedMember, roleBS)
                    msg += f"Assigned roles: {roleVerifiedMember.name}, {roleBS.name}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't add {roleVerifiedMember.name}, {roleBSMember.name}\n"

                try:
                    await member.remove_roles(newcomer)
                    msg += f"Removed roles: {newcomer.name}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't remove {newcomer.name}\n"

                if "name" in player.raw_data["club"] and "LA " in player.club.name:
                    try:
                        await member.add_roles(roleBSMember)
                        msg += f"Assigned roles: {roleBSMember.name}\n"
                    except discord.Forbidden:
                        msg += f":exclamation:Couldn't add {roleBSMember.name})\n"
                else:
                    try:
                        await member.add_roles(roleGuest)
                        msg += f"Assigned roles: {roleGuest.name}\n"
                    except discord.Forbidden:
                        msg += f":exclamation:Couldn't add {roleGuest.name})\n"
                await globalChat.send(f"<:LA:602901892141547540> {member.mention} welcome to LA Gaming!")
            except brawlstats.errors.NotFoundError as e:
                msg += "No player with this tag found, try again!"
            except brawlstats.errors.RequestError as e:
                msg += f"Brawl Stars API is offline, please try again later! ({str(e)})"
            except Exception as e:
                msg += f":exclamation:Error occured: {str(e)}\n"

        elif game.lower() == "cr":
            tag = tag.lower().replace('O', '0').replace(' ', '')
            if tag.startswith("#"):
                tag = tag.strip('#')
            try:
                player = await self.crapi.get_player("#" + tag)

                nick = f"{player.name} | {player.clan.name}" if player.clan is not None else f"{player.name}"
                try:
                    await member.edit(nick=nick[:31])
                    msg += f"Nickname changed: {nick[:31]}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change nickname of this user. ({nick[:31]})\n"

                await self.crconfig.user(member).tag.set(tag)

                try:
                    await member.add_roles(roleVerifiedMember, roleCR)
                    msg += f"Assigned roles: {roleVerifiedMember.name}, {roleCR}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't add {roleVerifiedMember.name}, {roleCR.name}\n"

                try:
                    await member.remove_roles(newcomer)
                    msg += f"Removed roles: {newcomer.name}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't add {newcomer.name}\n"

                la_clan = False
                if player.clan is not None:
                    clans = await self.crconfig.guild(ctx.guild).clans()
                    for k in clans.keys():
                        if player.clan.tag.replace("#", "") == clans[k]["tag"]:
                            la_clan = True

                if la_clan:
                    try:
                        await member.add_roles(roleCRMember)
                        msg += f"Assigned roles: {roleCRMember.name}\n"
                    except discord.Forbidden:
                        msg += f":exclamation:Couldn't add {roleCRMember.name})\n"
                else:
                    try:
                        await member.add_roles(roleGuest)
                        msg += f"Assigned roles: {roleGuest.name}\n"
                    except discord.Forbidden:
                        msg += f":exclamation:Couldn't add {roleGuest.name})\n"
                await globalChat.send(f"<:LA:602901892141547540> {member.mention} welcome to LA Gaming!")

            except clashroyale.NotFoundError as e:
                msg += "No player with this tag found, try again!"
            except clashroyale.RequestError as e:
                msg += f"Clash Royale API is offline, please try again later! ({str(e)})"
            except Exception as e:
                msg += f":exclamation:Error occured: {str(e)}\n"
        else:
            try:
                await member.add_roles(roleVerifiedMember)
                await member.add_roles(roleGuest)
                msg += f"Assigned roles: {roleVerifiedMember.name}, {roleGuest.name}\n"
            except discord.Forbidden:
                msg += f":exclamation:Couldn't change roles of this user. ({roleVerifiedMember.name}, {roleCRMember.name})\n"
            try:
                await member.remove_roles(newcomer)
                msg += f"Removed roles: {newcomer.name}\n"
            except discord.Forbidden:
                msg += f":exclamation:Couldn't remove roles of this user. ({newcomer.name})\n"
            await globalChat.send(f"<:LA:602901892141547540> {member.mention} welcome to LA Gaming!")
        
        await ctx.send(embed=discord.Embed(description=msg, color=discord.Colour.blue()))

    async def do_setup_LAFC(self, member):
        welcomingprocess = member.guild.get_role(673034397179445294)
        await member.add_roles(welcomingprocess)
        welcome = self.bot.get_channel(673026631362805770)
        sendTagEmbed = discord.Embed(title="Welcome to LA Fight Club!", description="To gain access to the rest of the server, send /setupLAFC and your Clash Royale tag in this channel.", colour=discord.Colour.blue())
        sendTagEmbed.set_image(url="https://i.imgur.com/Fc8uAWH.png")
        await welcome.send(member.mention)
        await welcome.send(embed=sendTagEmbed)
        
    @commands.guild_only()
    @commands.command(aliases=["setuplafc"])
    async def setupLAFC(self, ctx, tag, member: discord.Member = None):
        if ctx.channel.id != 673026631362805770:
            await ctx.send(embed=discord.Embed(description="This command can't be used in this channel.", colour=discord.Colour.red()))
            return
        globalChat = self.bot.get_channel(593248015729295362)
        if member == None:
            member = ctx.author
        welcomingprocess = member.guild.get_role(673034397179445294)
        msg = ""
        tag = tag.lower().replace('O', '0').replace(' ', '')
        if tag.startswith("#"):
            tag = tag.strip('#')
        try:
            player = await self.crapi.get_player("#" + tag)
            nick = f"{player.name} | {player.clan.name}" if player.clan is not None else f"{player.name}"
            try:
                await member.edit(nick=nick[:31])
                msg += f"Nickname changed: {nick[:31]}\n"
            except discord.Forbidden:
                msg += f":exclamation:Couldn't change nickname of this user. ({nick[:31]})\n"
            await self.crconfig.user(member).tag.set(tag)
            try:
                roleMember = member.guild.get_role(593299886167031809)
                await member.add_roles(roleMember)
                msg += f"Assigned roles: {roleMember.name}\n"
            except discord.Forbidden:
                msg += f":exclamation:Couldn't change roles of this user. ({roleMember.name})\n"
            trophyRole = None
            if player.trophies >= 8000:
                trophyRole = member.guild.get_role(600325526007054346)
            elif player.trophies >= 7000:
                trophyRole = member.guild.get_role(594960052604108811)
            elif player.trophies >= 6000:
                trophyRole = member.guild.get_role(594960023088660491)
            elif player.trophies >= 5000:
                trophyRole = member.guild.get_role(594959970181709828)
            elif player.trophies >= 4000:
                trophyRole = member.guild.get_role(594959895904649257)
            elif player.trophies >= 3000:
                trophyRole = member.guild.get_role(598396866299953165)
            if trophyRole is not None:
                try:
                    await member.add_roles(trophyRole)
                    msg += f"Assigned roles: {trophyRole.name}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change roles of this user. ({trophyRole.name})\n"
            if player.challengeMaxWins >= 20:
                try:
                    wins20Role = member.guild.get_role(593776990604230656)
                    await member.add_roles(wins20Role)
                    msg += f"Assigned roles: {wins20Role.name}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change roles of this user. ({wins20Role.name})\n"

        except clashroyale.NotFoundError as e:
            msg += "No player with this tag found, try again!\n"
        except ValueError as e:
            msg += f"**{str(e)}\nTry again or send a personal message to LA Modmail! ({str(e)})**\n"
        except clashroyale.RequestError as e:
            msg += f"Clash Royale API is offline, please try again later! ({str(e)})\n"
        except Exception as e:
            msg += f"**Something went wrong, please send a personal message to LA Modmail or try again! ({str(e)})**\n"
        await ctx.send(embed=discord.Embed(description=msg, colour=discord.Colour.blue()))

        await member.remove_roles(welcomingprocess)
        wlcm = ["Are you ready to fight?", "Do you have what it takes to become a champion?",
                "Ready to showcase your skill?", "Are you ready to prove yourself?"]
        await globalChat.send(
            f"<:lafclogo:603670041044582516> {member.mention} welcome to LA Fight Club! {choice(wlcm)}")

    async def do_setup_LABSevent(self, member):
        newcomer = member.guild.get_role(677272975938027540)
        await member.add_roles(newcomer)
        welcome = self.bot.get_channel(677272915779125269)
        sendTagEmbed = discord.Embed(title="Welcome to LA Events!", description="To gain access to the rest of the server, send /setupEvents and your Brawl Stars tag in this channel or «/setupEvents spectator» if you want to join as a spectator.", colour=discord.Colour.blue())
        sendTagEmbed.set_image(url="https://i.imgur.com/trjFkYP.png")
        await welcome.send(member.mention)
        await welcome.send(embed=sendTagEmbed)

    @commands.guild_only()
    @commands.command(aliases=["setupevents"])
    async def setupEvents(self, ctx, tag, member: discord.Member = None):
        if ctx.channel.id != 677272915779125269:
            await ctx.send(embed=discord.Embed(description="This command can't be used in this channel.", colour=discord.Colour.red()))
            return
        if member == None:
            member = ctx.author
        newcomer = member.guild.get_role(677272975938027540)
        msg = ""
        if tag != "spectator":
            selfroles = ctx.guild.get_channel(665566710492823554)
            guestselfroles = ctx.guild.get_channel(704890962421219339)
            tags = []
            guilds = await self.get_bs_config().all_guilds()
            events = guilds[654334199494606848]
            clubs = events["clubs"]
            for club in clubs:
                info = clubs[club]
                tagn = "#" + info["tag"]
                tags.append(tagn)

            tag = tag.lower().replace('O', '0')
            if tag.startswith("#"):
                tag = tag.strip('#')
            try:
                player = await self.ofcbsapi.get_player(tag)
                player_in_club = "name" in player.raw_data["club"]
                if player_in_club:
                    nick = f"{player.name} | {player.club.name}"
                elif not player_in_club:
                    nick = f"{player.name}"
                try:
                    await member.edit(nick=nick[:31])
                    msg += f"Nickname changed: {nick[:31]}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change nickname of this user. ({nick[:31]})\n"

                await self.get_bs_config().user(member).tag.set(tag)

                try:
                    LAMember = member.guild.get_role(654334569528688641)
                    guest = member.guild.get_role(701822453021802596)
                    if not player_in_club:
                        await member.add_roles(guest)
                        msg += f"Assigned roles: {guest.name}\n"
                        await guestselfroles.send(f"{member.mention}, take your regional roles to get pinged when a tourney is posted.", delete_after=10)
                    elif player_in_club and ("LA " in player.club.name or player.club.tag in tags):
                        await member.add_roles(LAMember)
                        msg += f"Assigned roles: {LAMember.name}\n"
                        await selfroles.send(f"{member.mention}, take your regional roles to get pinged when a tourney is posted.", delete_after=10)
                    else:
                        await member.add_roles(guest)
                        msg += f"Assigned roles: {guest.name}\n"
                        await guestselfroles.send(f"{member.mention}, take your regional roles to get pinged when a tourney is posted.",delete_after=10)
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change roles of this user.\n"

                try:
                    await member.remove_roles(newcomer)
                    msg += f"Removed roles: {newcomer.name}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't remove roles of this user. ({newcomer.name})\n"

                await member.remove_roles(newcomer)

            except brawlstats.errors.NotFoundError as e:
                await ctx.send("No player with this tag found, try again!")
                msg += f":exclamation:Error occured: {str(e)}\n"
            except brawlstats.errors.RequestError as e:
                await ctx.send(f"Brawl Stars API is offline, please try again later! ({str(e)})")
                msg += f":exclamation:Error occured: {str(e)}\n"
            except Exception as e:
                await ctx.send(f"**Something went wrong, please send a personal message to LA Modmail or try again!**")
                msg += f":exclamation:Error occured: {str(e)}\n"
        elif tag == "spectator":
            try:
                spectator = member.guild.get_role(671381405695082507)
                await member.add_roles(spectator)
                msg += f"Assigned roles: {spectator}\n"
            except discord.Forbidden:
                msg += f":exclamation:Couldn't change roles of this user.\n"
            try:
                await member.remove_roles(newcomer)
                msg += f"Removed roles: {newcomer.name}\n"
            except discord.Forbidden:
                msg += f":exclamation:Couldn't remove roles of this user. ({newcomer.name})\n"
        await ctx.send(embed=discord.Embed(description=msg, colour=discord.Colour.blue()))

    @tasks.loop(hours=24)
    async def sortrolesevents(self):
        try:
            ch = self.bot.get_channel(707246339133669436)
            await ch.trigger_typing()
            lamember = ch.guild.get_role(654334569528688641)
            guest = ch.guild.get_role(701822453021802596)
            es = ch.guild.get_role(654341494773383178)
            eu = ch.guild.get_role(654342521492865043)
            asia = ch.guild.get_role(654341631302041610)
            latam = ch.guild.get_role(654341685920399381)
            na = ch.guild.get_role(654341571331883010)
            bd = ch.guild.get_role(706469329679417366)
            newcomer = ch.guild.get_role(677272975938027540)
            esg = ch.guild.get_role(704951308154699858)
            eug = ch.guild.get_role(704951500782174268)
            asiag = ch.guild.get_role(704951716071866450)
            latamg = ch.guild.get_role(704951697990221876)
            nag = ch.guild.get_role(704951841229897758)
            error_counter = 0

            for member in ch.guild.members:
                if member.bot:
                    continue
                tag = await self.config.user(member).tag()
                if tag is None:
                    continue
                try:
                    player = await self.ofcbsapi.get_player(tag)
                    await asyncio.sleep(0.3)
                except brawlstats.errors.RequestError as e:
                    error_counter += 1
                    if error_counter == 5:
                        await ch.send(embed=discord.Embed(colour=discord.Colour.red(),
                                                          description=f"Stopping after 20 request errors! Displaying the last one:\n({str(e)})"))
                        break
                    await asyncio.sleep(1)
                    continue
                except Exception as e:
                    return await ch.send(embed=discord.Embed(colour=discord.Colour.red(),
                                                             description=f"**Something went wrong while requesting {tag}!**\n({str(e)})"))

                msg = ""
                player_in_club = "name" in player.raw_data["club"]

                tags = []
                guilds = await self.config.all_guilds()
                events = guilds[654334199494606848]
                clubs = events["clubs"]
                for club in clubs:
                    info = clubs[club]
                    tagn = "#" + info["tag"]
                    tags.append(tagn)

                if not player_in_club:
                    if es in member.roles:
                        msg += await self.removeroleifpresent(member, es)
                        msg += await self.addroleifnotpresent(member, esg)
                    elif eu in member.roles:
                        msg += await self.removeroleifpresent(member, eu)
                        msg += await self.addroleifnotpresent(member, eug)
                    elif asia in member.roles:
                        msg += await self.removeroleifpresent(member, asia)
                        msg += await self.addroleifnotpresent(member, asiag)
                    elif latam in member.roles:
                        msg += await self.removeroleifpresent(member, latam)
                        msg += await self.addroleifnotpresent(member, latamg)
                    elif na in member.roles:
                        msg += await self.removeroleifpresent(member, na)
                        msg += await self.addroleifnotpresent(member, nag)
                    elif bd in member.roles:
                        msg += await self.removeroleifpresent(member, bd)
                    msg += await self.removeroleifpresent(member, lamember, newcomer)
                    msg += await self.addroleifnotpresent(member, guest)

                if player_in_club and "LA " not in player.club.name and player.club.tag not in tags:
                    if es in member.roles:
                        msg += await self.removeroleifpresent(member, es)
                        msg += await self.addroleifnotpresent(member, esg)
                    elif eu in member.roles:
                        msg += await self.removeroleifpresent(member, eu)
                        msg += await self.addroleifnotpresent(member, eug)
                    elif asia in member.roles:
                        msg += await self.removeroleifpresent(member, asia)
                        msg += await self.addroleifnotpresent(member, asiag)
                    elif latam in member.roles:
                        msg += await self.removeroleifpresent(member, latam)
                        msg += await self.addroleifnotpresent(member, latamg)
                    elif na in member.roles:
                        msg += await self.removeroleifpresent(member, na)
                        msg += await self.addroleifnotpresent(member, nag)
                    elif bd in member.roles:
                        msg += await self.removeroleifpresent(member, bd)
                    msg += await self.removeroleifpresent(member, lamember, newcomer)
                    msg += await self.addroleifnotpresent(member, guest)

                if player_in_club and "LA " in player.club.name and player.club.tag not in tags:
                    if esg in member.roles:
                        msg += await self.removeroleifpresent(member, esg)
                        msg += await self.addroleifnotpresent(member, es)
                    elif eug in member.roles:
                        msg += await self.removeroleifpresent(member, eug)
                        msg += await self.addroleifnotpresent(member, eu)
                    elif asiag in member.roles:
                        msg += await self.removeroleifpresent(member, asiag)
                        msg += await self.addroleifnotpresent(member, asia)
                    elif latamg in member.roles:
                        msg += await self.removeroleifpresent(member, latamg)
                        msg += await self.addroleifnotpresent(member, latam)
                    elif nag in member.roles:
                        msg += await self.removeroleifpresent(member, nag)
                        msg += await self.addroleifnotpresent(member, na)
                    msg += await self.removeroleifpresent(member, guest, newcomer)
                    msg += await self.addroleifnotpresent(member, lamember)

                if player_in_club and player.club.tag in tags:
                    if esg in member.roles:
                        msg += await self.removeroleifpresent(member, esg)
                        msg += await self.addroleifnotpresent(member, es)
                    elif eug in member.roles:
                        msg += await self.removeroleifpresent(member, eug)
                        msg += await self.addroleifnotpresent(member, eu)
                    elif asiag in member.roles:
                        msg += await self.removeroleifpresent(member, asiag)
                        msg += await self.addroleifnotpresent(member, asia)
                    elif latamg in member.roles:
                        msg += await self.removeroleifpresent(member, latamg)
                        msg += await self.addroleifnotpresent(member, latam)
                    elif nag in member.roles:
                        msg += await self.removeroleifpresent(member, nag)
                        msg += await self.addroleifnotpresent(member, na)
                    msg += await self.removeroleifpresent(member, guest, newcomer)
                    msg += await self.addroleifnotpresent(member, lamember)
                if msg != "":
                    await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg, title=str(member)))
        except Exception as e:
            await ch.send(e)

    @sortrolesevents.before_loop
    async def before_sortrolesevents(self):
        await asyncio.sleep(5)
