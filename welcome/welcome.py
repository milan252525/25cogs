import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.chat_formatting import pagify
import clashroyale
import brawlstats
import asyncio
import time
from random import choice

class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.crconfig = Config.get_conf(None, identifier=2512325, cog_name="ClashRoyaleCog")
        self.bsconfig = Config.get_conf(None, identifier=5245652, cog_name="BrawlStarsCog")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == 440960893916807188 and not member.bot:
            await self.do_setup(member)
        if member.guild.id == 593248015729295360 and not member.bot:
            await self.do_setup_LAFC(member)
        if member.guild.id == 654334199494606848 and not member.bot:
            await self.do_setup_LABSevent(member)
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id == 440960893916807188 and not member.bot:
            welcomeCategory = discord.utils.get(member.guild.categories, id=598437481775497216)
            for ch in welcomeCategory.channels:
                if ch.topic == str(member.id):
                    await ch.delete(reason="User left.")
        if member.guild.id == 593248015729295360 and not member.bot:
            welcomeCategory = discord.utils.get(member.guild.categories, id=602906519100719115)
            for ch in welcomeCategory.channels:
                if ch.topic == str(member.id):
                    await ch.delete(reason="User left.")
        if member.guild.id == 654334199494606848 and not member.bot:
            welcomeCategory = discord.utils.get(member.guild.categories, id=654334199993466880)
            for ch in welcomeCategory.channels:
                if ch.topic == str(member.id):
                    await ch.delete(reason="User left.")


    async def initialize(self):
        crapikey = await self.bot.get_shared_api_tokens("crapi")
        if crapikey["api_key"] is None:
            raise ValueError("The Clash Royale API key has not been set.")
        self.crapi = clashroyale.OfficialAPI(crapikey["api_key"], is_async=True)
        
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.Client(ofcbsapikey["api_key"], is_async=True)

    # @commands.command(hidden=True)
    # async def detect(self, ctx):
    #     try:
    #         att = ctx.message.attachments[0]
    #         if att.filename[-3:] == "png":
    #             name = "todetect.png"
    #         elif att.filename[-3:] == "jpg":
    #             name = "todetect.jpg"
    #         elif att.filename[-4:] == "jpeg":
    #             name = "todetect.jpeg"
    #         await att.save(name)
    #         text = pytesseract.image_to_data(Image.open(name))
    #         print(text)
    #     except IndexError:
    #         await ctx.send("No image.")
            
    @commands.guild_only()
    @commands.command(hidden=True)
    async def setup(self, ctx, member:discord.Member = None):
        if member is None:
            member = ctx.author
        if ctx.guild.id == 440960893916807188:
            await self.do_setup(member)
        elif ctx.guild.id == 593248015729295360:
            await self.do_setup_LAFC(member)
        elif ctx.guild.id == 654334199494606848:
            await self.do_setup_LABSevent(member)
        else:
            await ctx.send("Can't use setup in this server!")

    async def do_setup(self, member):
        newcomer = member.guild.get_role(597767307397169173)
        await member.add_roles(newcomer)
        welcome = self.bot.get_channel(674348799673499671)
        welcomeEmbed = discord.Embed(colour=discord.Colour.blue())
        welcomeEmbed.set_image(url="https://i.imgur.com/wwhgP4f.png")
        welcomeEmbed2 = discord.Embed(colour=discord.Colour.blue())
        welcomeEmbed2.set_image(url="https://i.imgur.com/LOLUk7Q.png")
        welcomeEmbed3 = discord.Embed(colour=discord.Colour.blue())
        welcomeEmbed3.set_image(url="https://i.imgur.com/SkR1NsG.png")
        await welcome.send(member.mention, embed=welcomeEmbed)
        await welcome.send("We are a gamer run community devoted to enhancing the player experience. We offer comprehensive resources, guidance from veteran gamers, and involvement in a vibrant interactive online community that cater to both casual members and players looking for a more competitive edge. We have an eSports team and host frequent tournaments/events for cash prizes.", embed=welcomeEmbed2)
        await welcome.send("You can read about our mission statement and how we function at <#597812113888509962>.\nPlease follow our discord and gaming rules which can be viewed in detail at <#597789850749501441>.", embed=welcomeEmbed3)
        await welcome.send("To join the server with a CR tag, type /setupmain cr <CR tag> without brackets. To join the server with a BS tag, type /setupmain bs <BS tag> without brackets. To join the server with both BS and CR tag, type /setupmain cr,bs <CR tag>,<BS tag> without brackets.")

    @commands.command()
    @commands.guild_only()
    async def setupmain(self, ctx, game, tag, member: discord.Member = None):
        if ctx.channel.id != 674348799673499671:
            await ctx.send(embed=discord.Embed(description="This command can't be used in this channel.", colour=discord.Colour.red()))
            return
        if member == None:
            member = ctx.author
        newcomer = member.guild.get_role(597767307397169173)
        globalChat = self.bot.get_channel(556425378764423179)
        msg = ""
        if game.lower() == "bs":
            tag = tag.lower().replace('O', '0')
            if tag.startswith("#"):
                tag = tag.strip('#')
            try:
                player = await self.ofcbsapi.get_player(tag)
                nick = f"{player.name} | {player.club.name}" if player.club is not None else f"{player.name}"
                try:
                    await member.edit(nick=nick[:31])
                    msg += f"Nickname changed: {nick[:31]}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change nickname of this user. ({nick[:31]})\n"

                await self.bsconfig.user(member).tag.set(tag)

                try:
                    roleVerifiedMember = member.guild.get_role(597768235324145666)
                    roleBSMember = member.guild.get_role(524418759260241930)
                    await member.add_roles(roleVerifiedMember, roleBSMember)
                    msg += f"Assigned roles: {roleVerifiedMember.name}, {roleBSMember.name}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change roles of this user. ({roleVerifiedMember.name}, {roleBSMember.name})\n"

                try:
                    await member.remove_roles(newcomer)
                    msg += f"Removed roles: {newcomer.name}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't remove roles of this user. ({newcomer.name})\n"

                await globalChat.send(f"<:LA:602901892141547540> {member.mention} welcome to LA Gaming!")

            except brawlstats.errors.NotFoundError as e:
                await ctx.send("No player with this tag found, try again!")
                msg += f":exclamation:Error occured: {str(e)}\n"
            except brawlstats.errors.RequestError as e:
                await ctx.send(f"Brawl Stars API is offline, please try again later! ({str(e)})")
                msg += f":exclamation:Error occured: {str(e)}\n"
            except Exception as e:
                await ctx.send(
                    "**Something went wrong, please send a personal message to LA Modmail or try again!**")
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
                    roleVerifiedMember = member.guild.get_role(597768235324145666)
                    roleCRMember = member.guild.get_role(440982993327357963)
                    await member.add_roles(roleVerifiedMember, roleCRMember)
                    msg += f"Assigned roles: {roleVerifiedMember.name}, {roleCRMember.name}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change roles of this user. ({roleVerifiedMember.name}, {roleCRMember.name})\n"

                try:
                    await member.remove_roles(newcomer)
                    msg += f"Removed roles: {newcomer.name}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't remove roles of this user. ({newcomer.name})\n"

                await globalChat.send(f"<:LA:602901892141547540> {member.mention} welcome to LA Gaming!")

            except clashroyale.NotFoundError as e:
                await ctx.send("No player with this tag found, try again!")
                msg += f":exclamation:Error occured: {str(e)}\n"
            except ValueError as e:
                await ctx.send(f"**{str(e)}\nTry again or send a personal message to LA Modmail!**")
                msg += f":exclamation:Error occured: {str(e)}\n"
            except clashroyale.RequestError as e:
                await ctx.send(f"Clash Royale API is offline, please try again later! ({str(e)})")
                msg += f":exclamation:Error occured: {str(e)}\n"
            except Exception as e:
                await ctx.send(
                    "**Something went wrong, please send a personal message to LA Modmail or try again!**")
                msg += f":exclamation:Error occured: {str(e)}\n"
        elif game.lower() == "cr,bs":
            tags = tag.split(",")
            crtag = tags[0]
            bstag = tags[1]

            crtag = crtag.lower().replace('O', '0').replace(' ', '')
            if crtag.startswith("#"):
                crtag = crtag.strip('#')

            bstag = bstag.lower().replace('O', '0')
            if bstag.startswith("#"):
                bstag = bstag.strip('#')

            try:
                player = await self.crapi.get_player("#" + crtag)

                nick = f"{player.name} | {player.clan.name}" if player.clan is not None else f"{player.name}"
                try:
                    await member.edit(nick=nick[:31])
                    msg += f"Nickname changed: {nick[:31]}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change nickname of this user. ({nick[:31]})\n"

                await self.crconfig.user(member).tag.set(crtag)
                await self.bsconfig.user(member).tag.set(bstag)

                try:
                    roleVerifiedMember = member.guild.get_role(597768235324145666)
                    roleCRMember = member.guild.get_role(440982993327357963)
                    roleBSMember = member.guild.get_role(524418759260241930)
                    await member.add_roles(roleVerifiedMember, roleCRMember, roleBSMember)
                    msg += f"Assigned roles: {roleVerifiedMember.name}, {roleCRMember.name}, {roleBSMember.name}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change roles of this user. ({roleVerifiedMember.name}, {roleCRMember.name}, {roleBSMember.name})\n"

                try:
                    await member.remove_roles(newcomer)
                    msg += f"Removed roles: {newcomer.name}\n"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't remove roles of this user. ({newcomer.name})\n"

                await globalChat.send(f"<:LA:602901892141547540> {member.mention} welcome to LA Gaming!")

            except clashroyale.NotFoundError as e:
                await ctx.send("No player with this tag found, try again!")
                msg += f":exclamation:Error occured: {str(e)}\n"
            except ValueError as e:
                await ctx.send(f"**{str(e)}\nTry again or send a personal message to LA Modmail!**")
                msg += f":exclamation:Error occured: {str(e)}\n"
            except clashroyale.RequestError as e:
                await ctx.send(f"Clash Royale API is offline, please try again later! ({str(e)})")
                msg += f":exclamation:Error occured: {str(e)}\n"
            except brawlstats.errors.NotFoundError as e:
                await ctx.send("No player with this tag found, try again!")
                msg += f":exclamation:Error occured: {str(e)}\n"
            except brawlstats.errors.RequestError as e:
                await ctx.send(f"Brawl Stars API is offline, please try again later! ({str(e)})")
                msg += f":exclamation:Error occured: {str(e)}\n"
            except Exception as e:
                await ctx.send("**Something went wrong, please send a personal message to LA Modmail or try again!**")
                msg += f":exclamation:Error occured: {str(e)}\n"

        await ctx.send(embed=discord.Embed(description=msg, color=discord.Colour.blue()))

    async def do_setup_LAFC(self, member):
        welcomingprocess = member.guild.get_role(673034397179445294)
        await member.add_roles(welcomingprocess)
        welcome = self.bot.get_channel(673026631362805770)
        sendTagEmbed = discord.Embed(title="Welcome to LA Fight Club!", description="To gain access to the rest of the server, send /setupLAFC and your Clash Royale tag in this channel.", colour=discord.Colour.blue())
        sendTagEmbed.set_image(url="https://i.imgur.com/Fc8uAWH.png")
        await welcome.send(member.mention)
        await welcome.send(embed=sendTagEmbed)

    @commands.command()
    @commands.guild_only()
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

    @commands.command()
    @commands.guild_only()
    async def setupEvents(self, ctx, tag, member: discord.Member = None):
        if ctx.channel.id != 677272915779125269:
            await ctx.send(embed=discord.Embed(description="This command can't be used in this channel.", colour=discord.Colour.red()))
            return
        if member == None:
            member = ctx.author
        newcomer = member.guild.get_role(677272975938027540)
        msg = ""
        if tag != "spectator":
            tags = []
            guilds = await self.bsconfig.all_guilds()
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

                await self.bsconfig.user(member).tag.set(tag)

                try:
                    LAMember = member.guild.get_role(654334569528688641)
                    guest = member.guild.get_role(656506416911351848)
                    if not player_in_club:
                        await member.add_roles(guest)
                        msg += f"Assigned roles: {guest.name}\n"
                    elif player_in_club and ("LA " in player.club.name or player.club.tag in tags):
                        await member.add_roles(LAMember)
                        msg += f"Assigned roles: {LAMember.name}\n"
                    else:
                        await member.add_roles(guest)
                        msg += f"Assigned roles: {guest.name}\n"
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
            except ZeroDivisionError as e:
                await ctx.send(f"**Something went wrong, please send a personal message to LA Modmail or try again!**")
                msg += f":exclamation:Error occured: {str(e)}\n"
        elif tag == "spectator":
            try:
                spectator = member.guild.get_role(671381405695082507)
                await member.add_roles(spectator)
                msg += f"Assigned roles: {spectator}\n"
            except discord.Forbidden:
                msg += f":exclamation:Couldn't change roles of this user.\n"
        await ctx.send(embed=discord.Embed(description=msg, colour=discord.Colour.blue()))
