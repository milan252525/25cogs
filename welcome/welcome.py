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
            await self.do_setup_LABSevent(member, new = True)
    
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
        
        bsapikey = await self.bot.get_shared_api_tokens("bsapi")
        if bsapikey["api_key"] is None:
            raise ValueError("The Brawl Stars API key has not been set.")
        self.bsapi = brawlstats.BrawlAPI(bsapikey["api_key"], is_async=True, prevent_ratelimit=True)
        
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.OfficialAPI(ofcbsapikey["api_key"], is_async=True)

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
        await welcome.send("To join the server with a CR tag, type /setup cr <CR tag> without brackets. To join the server with a BS tag, type /setup bs <BS tag> without brackets. To join the server with both BS and CR tag, type /setup cr,bs <CR tag>,<BS tag> without brackets.")

    @commands.command()
    @commands.guild_only()
    async def setup(self, ctx, game, tag, member: discord.Member = None):
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
                    msg += f"Nickname changed: {nick[:31]}"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change nickname of this user. ({nick[:31]})"

                try:
                    roleVerifiedMember = member.guild.get_role(597768235324145666)
                    roleBSMember = member.guild.get_role(524418759260241930)
                    await member.add_roles(roleVerifiedMember, roleBSMember)
                    msg += f"Assigned roles: {roleVerifiedMember.name}, {roleBSMember.name}"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change roles of this user. ({roleVerifiedMember.name}, {roleBSMember.name})"

                try:
                    await member.remove_roles(newcomer)
                    msg += f"Removed roles: {newcomer.name}"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't remove roles of this user. ({newcomer.name})"

            except brawlstats.errors.NotFoundError as e:
                await ctx.send("No player with this tag found, try again!")
                msg += f":exclamation:Error occured: {str(e)}"
            except brawlstats.errors.RequestError as e:
                await ctx.send(f"Brawl Stars API is offline, please try again later! ({str(e)})")
                msg += f":exclamation:Error occured: {str(e)}"
            except Exception as e:
                await ctx.send(
                    "**Something went wrong, please send a personal message to LA Modmail or try again!**")
                msg += f":exclamation:Error occured: {str(e)}"
        elif game.lower() == "cr":
            tag = tag.lower().replace('O', '0').replace(' ', '')
            if tag.startswith("#"):
                tag = tag.strip('#')
            try:
                player = await self.crapi.get_player("#" + tag)

                nick = f"{player.name} | {player.clan.name}" if player.clan is not None else f"{player.name}"
                try:
                    await member.edit(nick=nick[:31])
                    msg += f"Nickname changed: {nick[:31]}"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change nickname of this user. ({nick[:31]})"

                await self.crconfig.user(member).tag.set(tag)

                try:
                    roleVerifiedMember = member.guild.get_role(597768235324145666)
                    roleCRMember = member.guild.get_role(440982993327357963)
                    await member.add_roles(roleVerifiedMember, roleCRMember)
                    msg += f"Assigned roles: {roleVerifiedMember.name}, {roleCRMember.name}"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change roles of this user. ({roleVerifiedMember.name}, {roleCRMember.name})"

                try:
                    await member.remove_roles(newcomer)
                    msg += f"Removed roles: {newcomer.name}"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't remove roles of this user. ({newcomer.name})"

            except clashroyale.NotFoundError as e:
                await ctx.send("No player with this tag found, try again!")
                msg += f":exclamation:Error occured: {str(e)}"
            except ValueError as e:
                await ctx.send(f"**{str(e)}\nTry again or send a personal message to LA Modmail!**")
                msg += f":exclamation:Error occured: {str(e)}"
            except clashroyale.RequestError as e:
                await ctx.send(f"Clash Royale API is offline, please try again later! ({str(e)})")
                msg += f":exclamation:Error occured: {str(e)}"
            except Exception as e:
                await ctx.send(
                    "**Something went wrong, please send a personal message to LA Modmail or try again!**")
                msg += f":exclamation:Error occured: {str(e)}"
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
                player = await self.crapi.get_player("#" + tag)

                nick = f"{player.name} | {player.clan.name}" if player.clan is not None else f"{player.name}"
                try:
                    await member.edit(nick=nick[:31])
                    msg += f"Nickname changed: {nick[:31]}"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change nickname of this user. ({nick[:31]})"

                await self.crconfig.user(member).tag.set(crtag)
                await self.config.user(member).tag.set(bstag)

                try:
                    roleVerifiedMember = member.guild.get_role(597768235324145666)
                    roleCRMember = member.guild.get_role(440982993327357963)
                    roleBSMember = member.guild.get_role(524418759260241930)
                    await member.add_roles(roleVerifiedMember, roleCRMember, roleBSMember)
                    msg += f"Assigned roles: {roleVerifiedMember.name}, {roleCRMember.name}"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't change roles of this user. ({roleVerifiedMember.name}, {roleCRMember.name}, {roleBSMember.name})"

                try:
                    await member.remove_roles(newcomer)
                    msg += f"Removed roles: {newcomer.name}"
                except discord.Forbidden:
                    msg += f":exclamation:Couldn't remove roles of this user. ({newcomer.name})"

            except clashroyale.NotFoundError as e:
                await ctx.send("No player with this tag found, try again!")
                msg += f":exclamation:Error occured: {str(e)}"
            except ValueError as e:
                await ctx.send(f"**{str(e)}\nTry again or send a personal message to LA Modmail!**")
                msg += f":exclamation:Error occured: {str(e)}"
            except clashroyale.RequestError as e:
                await ctx.send(f"Clash Royale API is offline, please try again later! ({str(e)})")
                msg += f":exclamation:Error occured: {str(e)}"
            except brawlstats.errors.NotFoundError as e:
                await ctx.send("No player with this tag found, try again!")
                msg += f":exclamation:Error occured: {str(e)}"
            except brawlstats.errors.RequestError as e:
                await ctx.send(f"Brawl Stars API is offline, please try again later! ({str(e)})")
                msg += f":exclamation:Error occured: {str(e)}"
            except Exception as e:
                await ctx.send("**Something went wrong, please send a personal message to LA Modmail or try again!**")
                msg += f":exclamation:Error occured: {str(e)}"

        await ctx.send(embed=discord.Embed(description=msg, color=discord.Colour.blue()))

        await globalChat.send(f"<:LA:602901892141547540> {member.mention} welcome to LA Gaming!")

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

    async def do_setup_LABSevent(self, member, new=False):
        welcomeCategory = discord.utils.get(member.guild.categories, id=654334199993466880)
        eventsStaff = member.guild.get_role(656072241808670730)
        overwrites = {member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                      member: discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                          read_message_history=True, add_reactions=True),
                      eventsStaff: discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                             read_message_history=True)}
        setupChannel = await member.guild.create_text_channel(member.name, category=welcomeCategory,
                                                              overwrites=overwrites, topic=f"{member.id}",
                                                              reason=f"Channel created for {member.display_name} role setup.")
        globalChat = self.bot.get_channel(656512846057963541)
        welcomeLog = self.bot.get_channel(654334199993466882)
        logMessages = []
        logMessages.append(await welcomeLog.send(f"--------------------\n__**{member.display_name}:**__"))

        async def appendLog(txt):
            count = 0
            for page in pagify(txt):
                if len(logMessages) < count + 1:
                    logMessages[count] = await welcomeLog.send(page)
                else:
                    await logMessages[count].edit(content=f"{logMessages[count].content}\n{page}")
                count += 1

        '''welcomeEmbed = discord.Embed(colour=discord.Colour.blue())
        welcomeEmbed.set_image(url="https://i.imgur.com/tG8Rio3.png")
        welcomeEmbed2 = discord.Embed(colour=discord.Colour.blue())
        welcomeEmbed2.set_image(url="https://i.imgur.com/wiY1LP4.png")
        await setupChannel.send(member.mention, embed=welcomeEmbed)
        await setupChannel.send(
            "Welcome to the **LA Fight Club**.\n\nWe are a gamer run community devoted to enhancing the player experience.\nLeaders of many clan families and esport organizations have come together to bring you this community.\n\nWe cater to players looking for a more competitive edge while keeping good sportsmanship.\nWe have frequent tournaments/events for cash prizes.",
            embed=welcomeEmbed2)
        await setupChannel.send(
            "You can read about how we function at <#595045518594408461>\nPlease follow our discord and gaming rules which can be viewed in detail at <#593310003591381005>")
        await asyncio.sleep(2)'''



        repeat = True
        while repeat:
            repeat = False
            text = "**CHOOSE ONE OF THE OPTIONS BELOW:**\n-----------------------------------------------------------\n<:BrawlStars:595528113929060374> **Save Brawl Stars account and join the server**\n-----------------------------------------------------------\n<:HelpIcon:598803665989402624> **Talk to support**\n-----------------------------------------------------------\n<:EyeSpect:598799975052345344> **Join as a spectator**\n-----------------------------------------------------------"
            chooseGameMessage = await setupChannel.send(text)
            await chooseGameMessage.add_reaction("<:BrawlStars:595528113929060374>")
            await chooseGameMessage.add_reaction("<:HelpIcon:598803665989402624>")
            await chooseGameMessage.add_reaction("<:EyeSpect:598799975052345344>")

            def check(reaction, user):
                return (user == member or user.id == 230947675837562880 or user.id == 359131399132807178) and str(reaction.emoji) in [
                    "<:BrawlStars:595528113929060374>", "<:HelpIcon:598803665989402624>", "<:EyeSpect:598799975052345344>"]

            reaction, _ = await self.bot.wait_for('reaction_add', check=check)

            if str(reaction.emoji) == "<:BrawlStars:595528113929060374>":
                await appendLog("Chosen game: Brawl Stars")

                tag = await self.bsconfig.user(member).tag()

                repeatSave = True
                while repeatSave:
                    repeatSave = False
                    accountConfirm = "Is this your account?"
                    accountFound = "**Brawl Stars** account with this tag found:"

                    if tag is not None:
                        accountConfirm = "Would you like to keep this account saved?"
                        accountFound = "I found this BS account assigned to your Discord account in a database:"
                    else:
                        sendTagEmbed = discord.Embed(title="Please tell me your Brawl Stars tag!",
                                                     colour=discord.Colour.blue())
                        sendTagEmbed.set_image(url="https://i.imgur.com/trjFkYP.png")
                        await setupChannel.send(embed=sendTagEmbed)

                        def checkmsg(m):
                            return m.channel == setupChannel and m.author == member

                        tagMessage = await self.bot.wait_for('message', check=checkmsg)
                        tag = tagMessage.content.lower().replace('O', '0').replace(' ', '')
                        if tag.startswith("#"):
                            tag = tag.strip('#')
                        await appendLog(f"Tag input: {tag}")

                    try:
                        player = await self.ofcbsapi.get_player(tag)
                        await appendLog(f"BS account found: {player.name}")
                        playerEmbed = discord.Embed(color=discord.Colour.blue())
                        playerEmbed.set_author(name=f"{player.name}", icon_url="https://i.imgur.com/ZwIP41S.png")
                        playerEmbed.add_field(name="Trophies",
                                              value=f"<:bstrophy:552558722770141204>{player.trophies}")
                        if player.club is not None:
                            playerEmbed.add_field(name="Club", value=f"<:bsband:600741378497970177> {player.club.name}")
                            club = await player.get_club()
                            for m in club.members:
                                if m.name == player.name:
                                    playerEmbed.add_field(name="Role",
                                                    value=f"<:role:614520101621989435> {m.role.capitalize()}")
                        else:
                            playerEmbed.add_field(name="Club", value="None")
                        playerEmbed.add_field(name=f"{accountConfirm} (Choose reaction)",
                                              value="<:yesconfirm:595535992329601034> Yes\t<:nocancel:595535992199315466> No",
                                              inline=False)
                        confirmMessage = await setupChannel.send(accountFound, embed=playerEmbed)
                        await confirmMessage.add_reaction("<:yesconfirm:595535992329601034>")
                        await confirmMessage.add_reaction("<:nocancel:595535992199315466>")

                        def ccheck(reaction, user):
                            return (user == member or user.id == 230947675837562880) and str(reaction.emoji) in [
                                "<:yesconfirm:595535992329601034>", "<:nocancel:595535992199315466>"]

                        reaction, _ = await self.bot.wait_for('reaction_add', check=ccheck)

                        if str(reaction.emoji) == "<:yesconfirm:595535992329601034>":
                            await appendLog(f"User's account: Yes")
                            nick = f"{player.name} | {player.clan.name}" if player.clan is not None else f"{player.name}"
                            try:
                                await member.edit(nick=nick[:31])
                                await appendLog(f"Nickname changed: {nick[:31]}")
                            except discord.Forbidden:
                                await appendLog(
                                    f":exclamation:Couldn't change nickname of this user. ({nick[:31]})")

                            await self.crconfig.user(member).tag.set(tag)
                            await appendLog("Saved tag: Brawl Stars")

                            try:
                                roleMember = member.guild.get_role(654334569528688641)
                                roleGuest = member.guild.get_role(656506416911351848)
                                if "LA " in player.club.name:
                                    await member.add_roles(roleMember)
                                elif "LA " not in player.club.name:
                                    await member.add_roles(roleGuest)
                                await appendLog(f"Assigned roles: {roleMember.name}")
                            except discord.Forbidden:
                                await appendLog(
                                    f":exclamation:Couldn't change roles of this user. ({roleMember.name})")



                            await setupChannel.send(
                                f"Your account has been saved!\n\nLet us know if you need anything by sending a personal message to LA Modmail.\n\nHead over to {globalChat.mention} to introduce yourself to our community!\n\n**Thank you, and enjoy your stay!**\n*- Legendary Alliance*")

                        elif str(reaction.emoji) == "<:nocancel:595535992199315466>":
                            await appendLog(f"User's account: No")
                            tag = None
                            repeatSave = True

                    except brawlstats.errors.NotFoundError:
                        repeat = True
                        await setupChannel.send("No player with this tag found, try again!")
                        await appendLog(f":exclamation:Error occured: {str(e)}")
                    except ValueError as e:
                        repeat = True
                        await setupChannel.send(
                            f"**{str(e)}\nTry again or send a personal message to LA Modmail!**")
                        await appendLog(f":exclamation:Error occured: {str(e)}")
                    except brawlstats.errors.RequestError as e:
                        repeat = True
                        await setupChannel.send(f"Brawl Stars API is offline, please try again later! ({str(e)})")
                        await appendLog(f":exclamation:Error occured: {str(e)}")
                    except Exception as e:
                        repeat = True
                        print(str(e))
                        await setupChannel.send(
                            "**Something went wrong, please send a personal message to LA Modmail or try again!**")
                        await appendLog(f":exclamation:Error occured: {str(e)}")

            elif str(reaction.emoji) == "<:HelpIcon:598803665989402624>":
                await appendLog("Chosen option: Talk to support")
                await setupChannel.send(
                    "You have stated that you require support, please send a DM to LA Modmail and state the problem you require support for. Once received our staff will be with you shortly!")
                await asyncio.sleep(5)
                repeat = True

            elif str(reaction.emoji) == "<:EyeSpect:598799975052345344>":
                await appendLog("Chosen option: Spectator")
                try:
                    roleSpectator = member.guild.get_role(671381405695082507)
                    await member.add_roles(roleSpectator)
                    await appendLog(f"Assigned roles: {roleSpectator.name}")
                except discord.Forbidden:
                    await appendLog(
                        f":exclamation:Couldn't change roles of this user. ({roleSpectator.name})")
                await setupChannel.send("You stated that you want to join as a spectator. Your roles were set accordingly.")



        '''if new:
            wlcm = ["Are you ready to fight?", "Do you have what it takes to become a champion?",
                    "Ready to showcase your skill?", "Are you ready to prove yourself?"]
            await globalChat.send(
                f"<:lafclogo:603670041044582516> {member.mention} welcome to LA Events! {choice(wlcm)}")'''
        await appendLog(f"**Finished**")
        await setupChannel.send(embed=discord.Embed(colour=discord.Colour.blue(),
                                                    description="Process finished, this channel will get deleted in 5 minutes!"))
        await asyncio.sleep(300)
        await setupChannel.delete(reason="Welcoming process finished.")
