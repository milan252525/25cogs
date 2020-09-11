import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.embed import randomize_colour
from redbot.core.utils.menus import menu, prev_page, next_page
from random import choice
import clashroyale
from typing import Union

class ClashRoyaleCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=2512325)
        default_user = {"tag" : None, "nick" : None}
        self.config.register_user(**default_user)
        default_guild = {"clans" : {}}
        self.config.register_guild(**default_guild)
        
    async def initialize(self):
        crapikey = await self.bot.get_shared_api_tokens("crapi")
        if crapikey["api_key"] is None:
            raise ValueError("The Clash Royale API key has not been set.")
        self.crapi = clashroyale.OfficialAPI(crapikey["api_key"], is_async=True)

    def badEmbed(self, text):
        bembed = discord.Embed(color=0xff0000)
        bembed.set_author(name=text, icon_url="https://i.imgur.com/FcFoynt.png")
        return bembed
        
    def goodEmbed(self, text):
        gembed = discord.Embed(color=0x45cafc)
        gembed.set_author(name=text, icon_url="https://i.imgur.com/qYmbGK6.png")
        return gembed
    
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.channel.id == 698556920830754939 and msg.author.id != 599286708911210557:
            try:
                id = int(msg.content)
                user = self.bot.get_user(int(msg.content))
                if user is None:
                    await (self.bot.get_channel(698556920830754939)).send(".")
                tag = await self.config.user(user).tag()
                if tag is None:
                    await (self.bot.get_channel(698556920830754939)).send(".")
                else:
                    await (self.bot.get_channel(698556920830754939)).send(tag.upper())
            except ValueError:
                pass

    @commands.command()
    async def crsave(self, ctx, tag, member: discord.Member = None):
        """Save your Clash Royale player tag"""
        if member == None:
            member = ctx.author        
        
        tag = tag.lower().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        try:
            player = await self.crapi.get_player("#" + tag)
            await self.config.user(member).tag.set(tag)
            await self.config.user(member).nick.set(player.name)
            await ctx.send(embed = self.goodEmbed("CR account {} was saved to {}".format(player.name, member.name)))
            
        except clashroyale.NotFoundError as e:
            await ctx.send(embed = self.badEmbed("No player with this tag found, try again!"))

        except clashroyale.RequestError as e:
            await ctx.send(embed = self.badEmbed(f"CR API is offline, please try again later! ({str(e)})"))
        
        except Exception as e:
            await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!**")
            
    @commands.has_permissions(administrator = True) 
    @commands.command()
    async def crunsave(self, ctx, member: discord.Member):
        await self.config.user(member).clear()
        await ctx.send("Done.")
           
    @commands.command(aliases=['rcr'])
    async def renamecr(self, ctx, member:discord.Member=None):
        await ctx.trigger_typing()
        prefix = ctx.prefix
        member = ctx.author if member is None else member
        
        tag = await self.config.user(member).tag()
        if tag is None:
            return await ctx.send(embed = self.badEmbed(f"This user has no tag saved! Use {prefix}crsave <tag>"))
        
        player = await self.crapi.get_player(tag)
        nick = f"{player.name} | {player.clan.name}" if player.clan is not None else f"{player.name}"
        try:
            await member.edit(nick=nick[:31])
            await ctx.send(f"Done! New nickname: `{nick[:31]}`")
        except discord.Forbidden:
            await ctx.send(f"I dont have permission to change nickname of this user!")
        except Exception as e:
            await ctx.send(f"Something went wrong: {str(e)}")
            
    @commands.command(aliases=['crp'])
    async def crprofile(self, ctx, member:Union[discord.Member, str]=None):
        """Clash Royale profile"""
        await ctx.trigger_typing()
        prefix = "/"
        tag = ""

        member = ctx.author if member is None else member

        if isinstance(member, discord.Member):
            tag = await self.config.user(member).tag()
            if tag is None:
                return await ctx.send(embed = self.badEmbed(f"This user has no tag saved! Use {prefix}crsave <tag>"))
        elif isinstance(member, str) and member.startswith("<"):
            id = member.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            try:
                member = discord.utils.get(ctx.guild.members, id=int(id))
                if member is not None:
                    tag = await self.config.user(member).tag()
                    if tag is None:
                        return await ctx.send(embed = self.badEmbed(f"This user has no tag saved! Use {prefix}crsave <tag>"))
            except ValueError:
                pass
        elif isinstance(member, str) and member.startswith("#"):
            tag = member.upper().replace('O', '0')
        elif isinstance(member, str):
            try:
                member = discord.utils.get(ctx.guild.members, id=int(member))
                if member is not None:
                    tag = await self.config.user(member).tag()
                    if tag is None:
                        return await ctx.send(embed = self.badEmbed(f"This user has no tag saved! Use {prefix}crsave <tag>"))
            except ValueError:
                member = discord.utils.get(ctx.guild.members, name=member)
                if member is not None:
                    tag = await self.config.user(member).tag()
                    if tag is None:
                        return await ctx.send(embed = self.badEmbed(f"This user has no tag saved! Use {prefix}crsave <tag>"))

        if tag is None or tag == "":
            desc = "/profile\n/profile @user\n/profile discord_name\n/profile discord_id\n/profile #CRTAG"
            embed = discord.Embed(title="Invalid argument!", colour=discord.Colour.red(), description=desc)
            return await ctx.send(embed=embed)
        try:
            player = await self.crapi.get_player(tag)
            chests = await self.crapi.get_player_chests(tag)
            
        except clashroyale.NotFoundError:
            return await ctx.send(embed = self.badEmbed("No player with this tag found, try again!"))

        except clashroyale.RequestError as e:
            return await ctx.send(embed = self.badEmbed(f"CR API is offline, please try again later! ({str(e)})"))
        
        except Exception as e:
            return await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!****")


        embed=discord.Embed()
        embed.set_author(name=f"{player.name} {player.tag}", icon_url="https://i.imgur.com/Qs0Ter9.png")
        embed.add_field(name="Trophies", value=f"<:trophycr:587316903001718789>{player.trophies}")
        embed.add_field(name="Highest Trophies", value=f"<:nicertrophy:587565339038973963>{player.bestTrophies}")
        embed.add_field(name="Level", value=f"<:level:451064038420381717>{player.expLevel}")
        embed.add_field(name="Arena", value=f"<:training:587566327204544512>{player.arena.name}")
        embed.add_field(name="Star Points", value=f"<:starpoints:737613015242768397>{player.starPoints}")
        if player.clan is not None:
            clanbadge = discord.utils.get(self.bot.emojis, name = str(player.clan.badgeId))
            embed.add_field(name="Clan", value=f"{clanbadge}{player.clan.name}")
            embed.add_field(name="Role", value=f"<:social:451063078096994304>{player.role.capitalize()}")
        embed.add_field(name="Total Games Played", value=f"<:swords:449650442033430538>{player.battleCount}")
        embed.add_field(name="Wins/Losses", value=f"<:starcr:587705837817036821>{player.wins}/{player.losses}")
        embed.add_field(name="Three Crown Wins", value=f"<:crownblue:449649785528516618>{player.threeCrownWins}")
        embed.add_field(name="War Day Wins", value=f"<:cw_win:449644364981993475>{player.warDayWins}")
        embed.add_field(name="Clan Cards Collected", value=f"<:cw_cards:449641339580317707>{player.clanCardsCollected}")
        embed.add_field(name="Max Challenge Wins", value=f"<:tournament:587706689357217822>{player.challengeMaxWins}")
        embed.add_field(name="Challenge Cards Won", value=f"<:cardcr:587702597855477770>{player.challengeCardsWon}")
        embed.add_field(name="Tournament Games Played", value=f"<:swords:449650442033430538>{player.tournamentBattleCount}")
        embed.add_field(name="Tournament Cards Won", value=f"<:cardcr:587702597855477770>{player.tournamentCardsWon}")
        if player.currentFavouriteCard is not None:
            embed.add_field(name="Favourite Card", value=f"<:epic:587708123087634457>{player.currentFavouriteCard.name}")
        embed.add_field(name="Total Donations", value=f"<:deck:451062749565550602>{player.totalDonations}")

        chests_msg = ""
        i = 0
        for chest in chests:
            emoji = discord.utils.get(self.bot.emojis, name = str(chest.name.lower().replace(" ", "")))
            chests_msg += f"{emoji}`{chest.index}`"
            if i == 8:
                chests_msg +="X"
            i+=1
        embed.add_field(name="Upcoming Chests", value=chests_msg.split("X")[0], inline=False)
        embed.add_field(name="Rare Chests", value=chests_msg.split("X")[1], inline=False)
        await ctx.send(embed=randomize_colour(embed))
        
        
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.command()
    async def clan(self, ctx, key: Union[discord.Member, str] = None, keyword = None):
        """View players clan or clan saved in a server"""
        await ctx.trigger_typing()
        
        key = ctx.author if key is None else key
        
        if isinstance(key, discord.Member):
            mtag = await self.config.user(ctx.author).tag()
            if mtag is None:
                return await ctx.send(embed=badEmbed(f"This user has no tag saved! Use {ctx.prefix}crsave <tag>"))
            try:
                player = await self.crapi.get_player(mtag)
                if player.clan is None:
                    return await ctx.send(embed = self.badEmbed("This user is not in a clan!"))
                tag = player.clan.tag
            except clashroyale.RequestError as e:
                return await ctx.send(embed = self.badEmbed(f"CR API is offline, please try again later! ({str(e)})"))
        elif key.startswith("#"):
            tag = key.upper().replace('O', '0')
        else:
            tag = await self.config.guild(ctx.guild).clans.get_raw(key.lower(), "tag", default=None)
            if tag is None:
                return await ctx.send(embed=badEmbed(f"{key.title()} isn't saved clan in this server!"))
            
        try:
            clan = await self.crapi.get_clan(tag)
            clan = clan.raw_data
            
        except clashroyale.NotFoundError:
            return await ctx.send(embed = self.badEmbed("No clan with this tag found, try again!"))

        except clashroyale.RequestError as e:
            return await ctx.send(embed = self.badEmbed(f"CR API is offline, please try again later! ({str(e)})"))
        
        if keyword is None:
            embed=discord.Embed(description=f"```{clan['description']}```")
            embed.set_author(name=f"{clan['name']} {clan['tag']}", icon_url=f"https://www.deckshop.pro/img/badges/{clan['badgeId']}.png")
            embed.add_field(name="Members", value=f"<:people:449645181826760734> {clan['members']}/50")
            embed.add_field(name="Required Trophies", value= f"<:trophycr:587316903001718789> {str(clan['requiredTrophies'])}")
            embed.add_field(name="Score", value= f"<:crstar:449647025999314954> {str(clan['clanScore'])}")
            embed.add_field(name="Clan War Trophies", value= f"<:cw_trophy:449640114423988234> {str(clan['clanWarTrophies'])}")
            embed.add_field(name="Type", value= f"<:bslock:552560387279814690> {clan['type'].title()}".replace("only", " Only"))
            embed.add_field(name="Location", value=f":earth_africa: {clan['location']['name']}")
            embed.add_field(name="Average Donations Per Week", value= f"<:deck:451062749565550602> {str(clan['donationsPerWeek'])}", inline=False)
            topm = ""
            for m in clan['memberList'][:5]:
                topm += f"<:trophycr:587316903001718789> `{m['trophies']}` {m['name']}\n"
            worstm = ""
            for m in clan['memberList'][-5:]:
                worstm += f"<:trophycr:587316903001718789> `{m['trophies']}` {m['name']}\n"
            embed.add_field(name="Top Members", value=topm, inline=True)
            embed.add_field(name="Lowest Members", value=worstm, inline=True)
            return await ctx.send(embed=randomize_colour(embed))  
        
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def clans(self, ctx, *, keyword: str = ""):
        """View all clans saved in this server"""
        offline = False
        low_clubs = False
        skip_errors = False
        reverse_order = False
        war = False
        await ctx.trigger_typing()
        await ctx.trigger_typing()

        if "offline" in keyword:
            offline = True
            keyword = keyword.replace("offline", "").strip()

        if "low" in keyword:
            low_clubs = True
            keyword = keyword.replace("low", "").strip()

        if "skiperrors" in keyword:
            skip_errors = True
            keyword = keyword.replace("skiperrors", "").strip()

        if "reverse" in keyword:
            reverse_order = True
            keyword = keyword.replace("reverse", "").strip()
                            
        if "war" in keyword:
            war = True
            keyword = keyword.replace("war", "").strip()
        
        if war and offline:
            return await ctx.send(embed = self.badEmbed(f"Can't combine war and offline keywords"))

        if len((await self.config.guild(ctx.guild).clans()).keys()) < 1:
            return await ctx.send(embed = self.badEmbed(f"This server has no clans saved. Save a clan by using {ctx.prefix}clans add!"))
                            
        saved_clans = await self.config.guild(ctx.guild).clans()
                             
        clans = []
        for key in saved_clans.keys():
            if offline:
                break
            try:
                if not war:
                    clan = await self.crapi.get_clan(saved_clans[key]["tag"])
                else:
                    url = f"https://api.clashroyale.com/v1/clans/%23{saved_clans[key]['tag'].strip('#')}/currentriverrace"
                    clan = await self.crapi._get_model(url, timeout=10)
            except clashroyale.RequestError as e:
                if skip_errors:
                    continue
                else:
                    offline = True
                    break
            clans.append(clan.raw_data)
                            
        embedFields = []

        if not offline:
            if not war:
                clans = sorted(clans, key=lambda sort: (sort['requiredTrophies'], sort['clanScore']), reverse=not reverse_order)

                for i in range(len(clans)):   
                    key = ""
                    for k in saved_clans.keys():
                        if clans[i]['tag'].replace("#", "") == saved_clans[k]["tag"]:
                            key = k

                    cemoji = discord.utils.get(self.bot.emojis, name = str(clans[i]['badgeId']))

                    saved_clans[key]['lastMemberCount'] = clans[i]['members']
                    saved_clans[key]['lastRequirement'] = clans[i]['requiredTrophies']
                    saved_clans[key]['lastScore'] = clans[i]['clanScore']
                    saved_clans[key]['lastPosition'] = i
                    saved_clans[key]['lastBadgeId'] = clans[i]['badgeId']
                    saved_clans[key]['warTrophies'] = clans[i]['clanWarTrophies']

                    info = saved_clans[key]['info'] if "info" in saved_clans[key] else ""

                    if low_clubs and len(clubs[i].members) >= 45:
                        continue

                    e_name = f"{str(cemoji)} {clans[i]['name']} [{key}] ({clans[i]['tag']}) {info}"
                    e_value = f"<:people:449645181826760734>`{clans[i]['members']}` <:trophycr:587316903001718789>`{clans[i]['requiredTrophies']}+` <:crstar:449647025999314954>`{clans[i]['clanScore']}` <:cw_trophy:449640114423988234>`{clans[i]['clanWarTrophies']}`"
                    embedFields.append([e_name, e_value])

                await self.config.guild(ctx.guild).set_raw("clans", value=saved_clans)
            else:
                clans = sorted(clans, key=lambda sort: (sort['clan']['fame'], sort['clan']['repairPoints']), reverse=not reverse_order)
                            
                for i in range(len(clans)):   
                    clan = clans[i]['clan']
                    key = ""
                    for k in saved_clans.keys():
                        if clan['tag'].replace("#", "") == saved_clans[k]["tag"]:
                            key = k

                    cemoji = discord.utils.get(self.bot.emojis, name = str(clan['badgeId']))
                    e_name = f"{str(cemoji)} {clan['name']} [{key}] ({clan['tag']})"
                    e_value = f"<:cwfame:753891694608646214>`{clan['fame']}` <:cwrepair:753891694956773447>`{clan['repairPoints']}` <:people:449645181826760734>`{len(clan['participants'])}`"
                    embedFields.append([e_name, e_value])

        else:
            offclans = []
            for k in saved_clans.keys():
                offclans.append([saved_clans[k]['lastPosition'], k])
            offclans = sorted(offclans, key=lambda x: x[0], reverse=reverse_order)

            for clan in offclans:
                ckey = clan[1]
                cscore = saved_clans[ckey]["lastScore"]
                cname = saved_clans[ckey]["name"]
                ctag = saved_clans[ckey]["tag"]
                cinfo = saved_clans[ckey]["info"]
                cmembers = saved_clans[ckey]["lastMemberCount"]
                creq = saved_clans[ckey]["lastRequirement"]
                ccw = saved_clans[ckey]["warTrophies"]
                             
                cemoji = discord.utils.get(self.bot.emojis, name = str(saved_clans[ckey]["lastBadgeId"]))
                            
                if low_clubs and cmembers >= 45:
                    continue

                e_name = f"{cemoji} {cname} [{ckey}] (#{ctag}) {cinfo}"
                e_value = f"<:people:449645181826760734>`{cmembers}` <:trophycr:587316903001718789>`{creq}+` <:crstar:449647025999314954>`{cscore}` <:cw_trophy:449640114423988234>`{ccw}`"
                embedFields.append([e_name, e_value])

        colour = choice([discord.Colour.green(),
                         discord.Colour.blue(),
                         discord.Colour.purple(),
                         discord.Colour.orange(),
                         discord.Colour.red(),
                         discord.Colour.teal()])
        embedsToSend = []                
        for i in range(0, len(embedFields), 8):
            embed = discord.Embed(colour=colour)
            embed.set_author(name=f"{ctx.guild.name} clans", icon_url=ctx.guild.icon_url)
            page = (i // 8) + 1
            footer =f"[{page}/{len(embedFields)//8+1}] API is offline, showing last saved data." if offline else f"[{page}/{len(embedFields)//8+1}] Do you need more info about a clan? Use {ctx.prefix}clan [key]"
            embed.set_footer(text = footer)
            for e in embedFields[i:i+8]:
                embed.add_field(name=e[0], value=e[1], inline=False)
            embedsToSend.append(embed)

        if len(embedsToSend) > 1:
            await menu(ctx, embedsToSend, {"⬅": prev_page, "➡": next_page, }, timeout=2000)
        elif len(embedsToSend) == 1:
            await ctx.send(embed=embedsToSend[0])
        else:
            await ctx.send("No clans found!")
          
    @commands.guild_only()
    @commands.has_permissions(administrator = True) 
    @clans.command(name="add")
    async def clans_add(self, ctx, key : str, tag : str):
        """
        Add a clan to /clans command

        key - key for the clan to be used in other commands
        tag - in-game tag of the clan
        """
        await ctx.trigger_typing()
        if tag.startswith("#"):
            tag = tag.strip('#').upper().replace('O', '0')
        
        if key in (await self.config.guild(ctx.guild).clans()).keys():
            return await ctx.send(embed = self.badEmbed("This clan is already saved!"))

        try:
            clan = await self.crapi.get_clan(tag)
            clan = clan.raw_data
            result = {
                "name" : clan['name'],
                "nick" : key.title(),
                "tag" : clan['tag'].replace("#", ""),
                "lastMemberCount" : clan['members'],
                "lastRequirement" : clan['requiredTrophies'],
                "lastScore" : clan['clanScore'],
                "info" : "",
                "warTrophies" : clan['clanWarTrophies']
                }
            key = key.lower()
            await self.config.guild(ctx.guild).clans.set_raw(key, value=result)
            await ctx.send(embed = self.goodEmbed(f"{clan['name']} was successfully saved in this server!"))

        except clashroyale.NotFoundError as e:
            await ctx.send(embed = self.badEmbed("No clan with this tag found, try again!"))

        except clashroyale.RequestError as e:
            await ctx.send(embed = self.badEmbed(f"CR API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!**")
                                                  
    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    @clans.command(name="remove")
    async def clans_remove(self, ctx, key : str):
        """
        Remove a clan from /clans command

        key - key for the clan used in commands
        """
        await ctx.trigger_typing()
        key = key.lower()
        
        try:
            name = await self.config.guild(ctx.guild).clans.get_raw(key, "name")
            await self.config.guild(ctx.guild).clans.clear_raw(key)
            await ctx.send(embed = self.goodEmbed(f"{name} was successfully removed from this server!"))
        except KeyError:
            await ctx.send(embed = self.badEmbed(f"{key.title()} isn't saved clan!"))

    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    @clans.command(name="info")
    async def clans_info(self, ctx, key : str, *, info : str = ""):
        """Edit clan info"""
        await ctx.trigger_typing()
        try:
            await self.config.guild(ctx.guild).clans.set_raw(key, "info", value=info)
            await ctx.send(embed = self.goodEmbed("Clan info successfully edited!"))
        except KeyError:
            await ctx.send(embed = self.badEmbed(f"{key.title()} isn't saved clan in this server!"))

    @commands.command()
    @commands.guild_only()
    async def refreshLAFC(self, ctx, member:discord.Member=None):
        if member == None:
            member = ctx.author
        msg = ""
        try:
            tag = await self.config.user(member).tag()
            player = await self.crapi.get_player("#" + tag)
            nick = f"{player.name} | {player.clan.name}" if player.clan is not None else f"{player.name}"
            try:
                await member.edit(nick=nick[:31])
                msg += f"Nickname changed: {nick[:31]}\n"
            except discord.Forbidden:
                msg += f":exclamation:Couldn't change nickname of this user. ({nick[:31]})\n"
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

    @commands.command()
    @commands.guild_only()
    async def userbytagcr(self, ctx, tag: str):
        """Find user with a specific tag saved"""
        tag = tag.lower().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        for user in (await self.config.all_users()):
            person = self.bot.get_user(user)
            if person is not None:
                if (await self.config.user(person).tag()) == tag:
                    return await ctx.send(f"This tag belongs to **{str(person)}**.")
        await ctx.send("This tag is either not saved or invalid.")
