import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.embed import randomize_colour
from redbot.core.utils.menus import menu, prev_page, next_page
from discord.ext import tasks
from random import choice
import asyncio
import brawlstats
from typing import Union

class BrawlStarsCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=5245652)
        default_user = {"tag" : None}
        self.config.register_user(**default_user)
        default_guild = {"clubs" : {}}
        self.config.register_guild(**default_guild)
        self.sortroles.start()
        
    async def cog_unload(self):
        self.sortroles.cancel()
        await self.bsapi.close()
        await self.ofcbsapi.close()
        
    async def initialize(self):
        bsapikey = await self.bot.db.api_tokens.get_raw("bsapi", default={"api_key": None})
        if bsapikey["api_key"] is None:
            raise ValueError("The Brawl Stars API key has not been set. Use [p]set api bsapi api_key,YOURAPIKEY")
        self.bsapi = brawlstats.BrawlAPI(bsapikey["api_key"], is_async=True, prevent_ratelimit=True)
        ofcbsapikey = await self.bot.db.api_tokens.get_raw("ofcbsapi", default={"api_key": None})
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set. Use [p]set api ofcbsapi api_key,YOURAPIKEY")
        self.ofcbsapi = brawlstats.OfficialAPI(ofcbsapikey["api_key"], is_async=True)
        
    def badEmbed(self, text):
        bembed = discord.Embed(color=0xff0000)
        bembed.set_author(name=text, icon_url="https://i.imgur.com/FcFoynt.png")
        return bembed
        
    def goodEmbed(self, text):
        gembed = discord.Embed(color=0x45cafc)
        gembed.set_author(name=text, icon_url="https://i.imgur.com/qYmbGK6.png")
        return gembed
    
    def get_league_emoji(self, trophies : int):
        if trophies < 500:
            return "<:league_icon_00:553294108802678787>"
        elif trophies < 1000:
            return "<:league_icon_01:553294108735569921>"
        elif trophies < 2000:
            return "<:league_icon_02:553294109167583296>"
        elif trophies < 3000:
            return "<:league_icon_03:553294109264052226>"
        elif trophies < 4000:
            return "<:league_icon_04:553294344413511682>"
        elif trophies < 6000:
            return "<:league_icon_05:553294344912764959>"
        elif trophies < 8000:
            return "<:league_icon_06:553294344841461775>"
        elif trophies < 10000:
            return "<:league_icon_07:553294109515972640>"
        else:
            return "<:league_icon_08:553294109217914910>"
        
    def remove_codes(self, text : str):
        toremove = ["</c>", "<c1>", "<c2>", "<c3>", "<c4>", "<c5>", "<c6>", "<c7>", "<c8>", "<c9>", "<c0>"]
        for code in toremove:
            text = text.replace(code, "")
        return text

    @commands.command(aliases=['bssave'])
    async def save(self, ctx, tag, member: discord.Member = None):
        """Save your Brawl Stars player tag"""
        if member == None:
            member = ctx.author        
        
        tag = tag.lower().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        try:
            player = await self.ofcbsapi.get_player(tag)
            await self.config.user(member).tag.set(tag.replace("#", ""))
            await ctx.send(embed = self.goodEmbed("BS account {} was saved to {}".format(player.name, member.name)))
            
        except brawlstats.errors.NotFoundError:
            await ctx.send(embed = self.badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            await ctx.send(embed = self.badEmbed(f"BS API is offline, please try again later! ({str(e)})"))
        
        except Exception as e:
            await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!****")
    
    @commands.command(aliases=['rbs'])
    async def renamebs(self, ctx, member:discord.Member=None):
        await ctx.trigger_typing()
        prefix = ctx.prefix
        member = ctx.author if member is None else member
        
        tag = await self.config.user(member).tag()
        if tag is None:
            return await ctx.send(embed = self.badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))
        
        player = await self.ofcbsapi.get_player(tag)
        nick = f"{player.name} | {player.club.name}" if player.club is not None else f"{player.name}"
        try:
            await member.edit(nick=nick[:31])
            await ctx.send(f"Done! New nickname: `{nick[:31]}`")
        except discord.Forbidden:
            await ctx.send(f"I dont have permission to change nickname of this user!")
        except Exception as e:
            await ctx.send(f"Something went wrong: {str(e)}")
    
    @commands.command(aliases=['p', 'bsp'])
    async def profile(self, ctx, *, member:Union[discord.Member, str]=None):
        """Brawl Stars profile"""
        await ctx.trigger_typing()
        prefix = ctx.prefix
        tag = ""

        member = ctx.author if member is None else member

        if isinstance(member, discord.Member):
            tag = await self.config.user(member).tag()
            if tag is None:
                return await ctx.send(embed = self.badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))
        elif isinstance(member, str) and member.startswith("<"):
            id = member.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            try:
                member = discord.utils.get(ctx.guild.members, id=int(id))
                if member is not None:
                    tag = await self.config.user(member).tag()
                    if tag is None:
                        return await ctx.send(embed = self.badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))
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
                        return await ctx.send(embed = self.badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))
            except ValueError:
                member = discord.utils.get(ctx.guild.members, name=member)
                if member is not None:
                    tag = await self.config.user(member).tag()
                    if tag is None:
                        return await ctx.send(embed = self.badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))

        if tag is None or tag == "":
            desc = "/p\n/bsprofile @user\n/p discord_name\n/p discord_id\n/p #CRTAG"
            embed = discord.Embed(title="Invalid argument!", colour=discord.Colour.red(), description=desc)
            return await ctx.send(embed=embed)
        try:
            player = await self.ofcbsapi.get_player(tag)
            
        except brawlstats.errors.NotFoundError:
            return await ctx.send(embed = self.badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed = self.badEmbed(f"BS API is offline, please try again later! ({str(e)})"))
        
        except Exception as e:
            return await ctx.send("****Something went wrong, please send a personal message to LA Modmail bot or try again!****")

        colour = player.name_color.replace("0x", "")
        embed=discord.Embed(color=discord.Colour.from_rgb(int(colour[0:2], 16), int(colour[2:4], 16), int(colour[4:6], 16)))
        embed.set_author(name=f"{player.name} {player.raw_data['tag']}", icon_url="https://i.imgur.com/ZwIP41S.png")
        embed.add_field(name="Trophies", value=f"{self.get_league_emoji(player.trophies)} {player.trophies}")
        embed.add_field(name="Highest Trophies", value=f"<:totaltrophies:614517396111097866> {player.highest_trophies}")
        embed.add_field(name="Level", value=f"<:exp:614517287809974405> {player.exp_level}")
        embed.add_field(name="Unlocked Brawlers", value=f"<:brawlers:614518101983232020> {len(player.brawlers)}")
        if player.club.tag is not None:
            embed.add_field(name="Club", value=f"<:bsband:600741378497970177> {player.club.name}")
            club = await player.get_club()
            for m in club.members:
                if m.tag == player.raw_data['tag']:
                    embed.add_field(name="Role", value=f"<:role:614520101621989435> {m.role.capitalize()}")
        embed.add_field(name="3v3 Wins", value=f"<:3v3:614519914815815693> {player.raw_data['3vs3Victories']}")
        embed.add_field(name="Solo SD Wins", value=f"<:sd:614517124219666453> {player.solo_victories}")
        embed.add_field(name="Duo SD Wins", value=f"<:duosd:614517166997372972> {player.duo_victories}")
        embed.add_field(name="Best Time in Robo Rumble", value=f"<:roborumble:614516967092781076> {player.best_robo_rumble_time//60}:{str(player.best_robo_rumble_time%60).rjust(2, '0')}")
        embed.add_field(name="Best Time as Big Brawler", value=f"<:biggame:614517022323245056> {player.best_time_as_big_brawler//60}:{str(player.best_time_as_big_brawler%60).rjust(2, '0')}")
        if "powerPlayPoints" in player.raw_data:     
            embed.add_field(name="Power Play Points", value=f"<:powertrophies:661266876235513867> {player.raw_data['powerPlayPoints']}")
        else:
            embed.add_field(name="Power Play Points", value=f"<:powertrophies:661266876235513867> 0")
        if "highestPowerPlayPoints" in player.raw_data:          
            embed.add_field(name="Highest PP Points", value=f"<:powertrophies:661266876235513867> {player.raw_data['highestPowerPlayPoints']}")
        embed.add_field(name="Qualified For Championship", value=f"<:powertrophies:661266876235513867> {player.raw_data['isQualifiedFromChampionshipChallenge']}")
        await ctx.send(embed=embed)

    @commands.command()
    async def club(self, ctx, key:Union[discord.Member, str]=None):
        await ctx.trigger_typing()
        if key == None:
            mtag = await self.config.user(ctx.author).tag()
            if mtag is None:
                return await ctx.send(embed = self.badEmbed(f"You have no tag saved! Use {ctx.prefix}bssave <tag>"))
            try:
                player = await self.ofcbsapi.get_player(mtag)
                if not player.club.tag:
                    return await ctx.send("This user is not in a club!")
                tag = player.club.tag
            except brawlstats.errors.RequestError as e:
                await ctx.send(embed = self.badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        elif isinstance(key, discord.Member):
            member=key
            mtag = await self.config.user(member).tag()
            if mtag is None:
                return await ctx.send(embed = self.badEmbed(f"This user has no tag saved! Use {ctx.prefix}bssave <tag>"))
            try:
                player = await self.ofcbsapi.get_player(mtag)
                if not player.club.tag:
                    return await ctx.send("This user is not in a club!")
                tag = player.club.tag
            except brawlstats.errors.RequestError as e:
                await ctx.send(embed = self.badEmbed(f"BS API is offline, please try again later! ({str(e)})"))
        else:
            tag = await self.config.guild(ctx.guild).clubs.get_raw(key.lower(), "tag", default=None)
            if tag is None:
                return await ctx.send(embed = self.badEmbed(f"{key.title()} isn't saved club in this server!"))
        try:
            club = await self.ofcbsapi.get_club(tag)
        
        except brawlstats.errors.RequestError as e:
            await ctx.send(embed = self.badEmbed(f"BS API is offline, please try again later! ({str(e)})"))
            return
        
        embed=discord.Embed(description=f"```{self.remove_codes(club.description)}```")
        embed.set_author(name=f"{club.name} {club.tag}")
        embed.add_field(name="Total Trophies", value= f"<:bstrophy:552558722770141204> `{club.trophies}`")
        embed.add_field(name="Required Trophies", value= f"{self.get_league_emoji(club.required_trophies)} `{club.required_trophies}`")
        embed.add_field(name="Average Trophies", value= f"<:bstrophy:552558722770141204> `{club.trophies//len(club.members)}`")
        for m in club.members:
            if m.role == "president":
                embed.add_field(name="President", value= f"{self.get_league_emoji(m.trophies)}`{m.trophies}` {m.name}")
                break
        embed.add_field(name="Members", value=f"<:icon_gameroom:553299647729238016> {len(club.members)}/100")
        embed.add_field(name="Status", value= f"<:bslock:552560387279814690> {club.type.title()}") 
        topm = ""
        for i in range(5):
            try:
                topm += f"{self.get_league_emoji(club.members[i].trophies)}`{club.members[i].trophies}` {self.remove_codes(club.members[i].name)}\n"
            except IndexError:
                pass
        worstm = ""
        for i in range(5):
            try:
                worstm += f"{self.get_league_emoji(club.members[len(club.members)-5+i].trophies)}`{club.members[len(club.members)-5+i].trophies}` {self.remove_codes(club.members[len(club.members)-5+i].name)}\n"
            except IndexError:
                pass
        embed.add_field(name = "Top Members", value = topm, inline = True)
        embed.add_field(name = "Lowest Members", value = worstm, inline = True)
        return await ctx.send(embed=randomize_colour(embed))            
            

    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def clubs(self, ctx, key:str=None):
        """View all clubs saved in this server"""
        offline = False
        await ctx.trigger_typing()

        if key == "forceoffline":
            offline = True
            key = None        
        
        if len((await self.config.guild(ctx.guild).clubs()).keys()) < 1:
            return await ctx.send(embed = self.badEmbed(f"This server has no clubs saved. Save a club by using {ctx.prefix}clubs add!"))
                                
        try:
            try:
                clubs = []
                for key in (await self.config.guild(ctx.guild).clubs()).keys():
                    club = await self.ofcbsapi.get_club(await self.config.guild(ctx.guild).clubs.get_raw(key, "tag"))
                    clubs.append(club)
                    #await asyncio.sleep(1)
            except brawlstats.errors.RequestError as e:
                offline = True
            
            embedFields = []
            
            if not offline:
                clubs = sorted(clubs, key=lambda sort: (sort.trophies), reverse=True)
                
                for i in range(len(clubs)):   
                    key = ""
                    for k in (await self.config.guild(ctx.guild).clubs()).keys():
                        if clubs[i].tag.replace("#", "") == await self.config.guild(ctx.guild).clubs.get_raw(k, "tag"):
                            key = k
                    
                    await self.config.guild(ctx.guild).clubs.set_raw(key, 'lastMemberCount', value=len(clubs[i].members))            
                    await self.config.guild(ctx.guild).clubs.set_raw(key, 'lastRequirement', value=clubs[i].required_trophies)   
                    await self.config.guild(ctx.guild).clubs.set_raw(key, 'lastScore', value=clubs[i].trophies)               
                    await self.config.guild(ctx.guild).clubs.set_raw(key, 'lastPosition', value=i)                 
                   
                    info = await self.config.guild(ctx.guild).clubs.get_raw(key, "info", default="")
                    e_name = f"<:bsband:600741378497970177> {clubs[i].name} [{key}] {clubs[i].tag} {info}"
                    e_value = f"<:bstrophy:552558722770141204>`{clubs[i].trophies}` {self.get_league_emoji(clubs[i].required_trophies)}`{clubs[i].required_trophies}+` <:icon_gameroom:553299647729238016>`{len(clubs[i].members)}`"
                    embedFields.append([e_name, e_value])
            
            else:
                offclubs = []
                for k in (await self.config.guild(ctx.guild).clubs()).keys():
                    offclubs.append([await self.config.guild(ctx.guild).clubs.get_raw(k, "lastPosition"), k])
                offclubs= sorted(offclubs, key=lambda x: x[0])
                                
                for club in offclubs:
                    ckey = club[1]
                    cscore = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "lastScore")
                    cname = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "name")
                    ctag = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "tag")
                    cinfo = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "info")
                    cmembers = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "lastMemberCount")
                    creq = await self.config.guild(ctx.guild).clubs.get_raw(ckey, "lastRequirement")       
                    #cemoji = discord.utils.get(self.bot.emojis, name = str(await self.config.guild(ctx.guild).clans.get_raw(ckey, "lastBadgeId")))
                    
                    e_name = f"<:bsband:600741378497970177> {cname} [{ckey}] #{ctag} {cinfo}"
                    e_value = f"<:bstrophy:552558722770141204>`{cscore}` {self.get_league_emoji(creq)}`{creq}+` <:icon_gameroom:553299647729238016>`{cmembers}` "
                    embedFields.append([e_name, e_value])
            
            colour = choice([discord.Colour.green(), discord.Colour.blue(), discord.Colour.purple(), discord.Colour.orange(), discord.Colour.red(), discord.Colour.teal()])
            embedsToSend = []                
            for i in range(0, len(embedFields), 8):
                embed = discord.Embed(colour=colour)
                embed.set_author(name=f"{ctx.guild.name} clubs", icon_url=ctx.guild.icon_url)
                footer = "<:offline:642094554019004416> API is offline, showing last saved data." if offline else f"Do you need more info about a club? Use {ctx.prefix}club [key]"
                embed.set_footer(text = footer)
                for e in embedFields[i:i+8]:
                    embed.add_field(name=e[0], value=e[1], inline=False)
                embedsToSend.append(embed)
                         
            if len(embedsToSend) > 1:                   
                await menu(ctx, embedsToSend, {"⬅": prev_page, "➡": next_page,} , timeout=600)
            else:
                await ctx.send(embed=embedsToSend[0])
                                
        except ZeroDivisionError as e:
            return await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!**")
        
    @commands.guild_only()
    @commands.has_permissions(administrator = True) 
    @clubs.command(name="add")
    async def clans_add(self, ctx, key : str, tag : str):
        """
        Add a club to /clubs command
        key - key for the club to be used in other commands
        tag - in-game tag of the club
        """
        await ctx.trigger_typing()
        if tag.startswith("#"):
            tag = tag.strip('#').upper().replace('O', '0')
        
        if key in (await self.config.guild(ctx.guild).clubs()).keys():
            return await ctx.send(embed = self.badEmbed("This club is already saved!"))

        try:
            club = await self.ofcbsapi.get_club(tag)
            result = {
                "name" : club.name,
                "nick" : key.title(),
                "tag" : club.tag.replace("#", ""),
                "lastMemberCount" : club.members_count,
                "lastRequirement" : club.required_trophies,
                "lastScore" : club.trophies,
                "info" : ""
                }
            key = key.lower()
            await self.config.guild(ctx.guild).clubs.set_raw(key, value=result)
            await ctx.send(embed = self.goodEmbed(f"{club.name} was successfully saved in this server!"))

        except brawlstats.errors.NotFoundError as e:
            await ctx.send(embed = self.badEmbed("No club with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            await ctx.send(embed = self.badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send("**Something went wrong, please send a personal message to LA Modmail bot or try again!**")

    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    @clubs.command(name="remove")
    async def clubs_remove(self, ctx, key : str):
        """
        Remove a club from /clubs command
        key - key for the club used in commands
        """
        await ctx.trigger_typing()
        key = key.lower()
        
        try:
            name = await self.config.guild(ctx.guild).clubs.get_raw(key, "name")
            await self.config.guild(ctx.guild).clubs.clear_raw(key)
            await ctx.send(embed = self.goodEmbed(f"{name} was successfully removed from this server!"))
        except KeyError:
            await ctx.send(embed = self.badEmbed(f"{key.title()} isn't saved club!"))

    @commands.guild_only()
    @commands.has_permissions(administrator = True)
    @clubs.command(name="info")
    async def clubs_info(self, ctx, key : str, *, info : str = ""):
        """Edit club info"""
        await ctx.trigger_typing()
        try:
            await self.config.guild(ctx.guild).clubs.set_raw(key, "info", value=info)
            await ctx.send(embed = self.goodEmbed("Club info successfully edited!"))
        except KeyError:
            await ctx.send(embed = self.badEmbed(f"{key.title()} isn't saved club in this server!"))

    async def removeroleifpresent(self, member: discord.Member, role: discord.Role):
        if role in member.roles:
            await member.remove_roles(role)
            return f"Removed **{str(role)}** from **{str(member)}**\n"
        return ""

    async def addroleifnotpresent(self, member: discord.Member, role: discord.Role):
        if role not in member.roles:
            await member.add_roles(role)
            return f"Added **{str(role)}** to **{str(member)}**\n"
        return ""
            
    @tasks.loop(hours=4)
    async def sortroles(self):
        ch = self.bot.get_channel(653295573872672810)
        await ch.trigger_typing()
        labs = discord.utils.get(ch.guild.roles, id=576028728052809728)
        guest = discord.utils.get(ch.guild.roles, id=578260960981286923)
        newcomer = discord.utils.get(ch.guild.roles, id=534461445656543255)
        brawlstars = discord.utils.get(ch.guild.roles, id=576002604740378629)
        vp = discord.utils.get(ch.guild.roles, id=536993652648574976)
        pres = discord.utils.get(ch.guild.roles, id=536993632918568991)
        for member in ch.guild.members:
            if guest in member.roles or member.bot:
                continue
            tag = await self.config.user(member).tag()
            if tag is None:
                continue
            try:
                player = await self.ofcbsapi.get_player(tag)
                await asyncio.sleep(0.1)

            except brawlstats.errors.RequestError as e:
                await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=f"BS API is offline ({str(e)})"))
                break

            except Exception as e:
                return await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=f"**Something went wrong while requesting {tag}!**"))

            memberrole = None
            club = ""
            msg = ""
            memberroles = []
            for role in member.roles:
                if role.name.startswith('LA '):
                    memberroles.append(role)

            if len(memberroles) > 1:
                toberemoved = ", ".join([str(r) for r in memberroles])
                msg += f"**{str(member)}** has more than one club role. Removing **{toberemoved}**"
                for role in memberroles:
                    await self.removeroleifpresent(member, role)
            elif len(memberroles) == 1:
                memberrole = memberroles[0]
                club = memberrole.name

            if newcomer in member.roles: #newcomer -> member
                if "club" not in player.raw_data or 'LA ' not in player.club.name:
                    msg += await self.removeroleifpresent(member, newcomer)
                    msg += await self.addroleifnotpresent(member, brawlstars)
                    msg += await self.addroleifnotpresent(member, guest)
                    await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))
                elif "club" in player.raw_data and 'LA ' in player.club.name:
                    msg += await self.removeroleifpresent(member, newcomer)
                    msg += await self.addroleifnotpresent(member, brawlstars)
                    msg += await self.addroleifnotpresent(member, labs)
                    rolefound = False
                    for r in ch.guild.roles:
                        if " ".join(r.name.split(' ', 2)[:2]) == player.club.name:
                            rolefound = True
                            msg += await self.addroleifnotpresent(member, r)
                            '''if player.club.role == 'Vice President':
                                msg += await self.addroleifnotpresent(member, vp)
                            elif player.club.role == 'President':
                                msg += await self.addroleifnotpresent(member, pres)'''
                    if not rolefound:
                        msg += f"Role for the club **{player.club.name}** not found.\n"
            elif ("club" not in player.raw_data or 'LA ' not in player.club.name) and memberrole is not None: #member -> guest
                msg += await self.removeroleifpresent(member, memberrole)
                msg += await self.removeroleifpresent(member, labs)
                msg += await self.removeroleifpresent(member, vp)
                msg += await self.removeroleifpresent(member, pres)
                msg += await self.addroleifnotpresent(member, guest)
            elif memberrole is None and "club" in player.raw_data and 'LA ' in player.club.name: #guest -> member
                rolefound = False
                for r in ch.guild.roles:
                    if " ".join(r.name.split(' ', 2)[:2]) == player.club.name:
                        rolefound = True
                        msg += await self.addroleifnotpresent(member, r)
                        '''if player.club.role == 'Vice President':
                            msg += await self.addroleifnotpresent(member, vp)
                        elif player.club.role == 'President':
                            msg += await self.addroleifnotpresent(member, pres)
                        elif player.club.role == 'Member' or player.club.role == 'Senior':
                            msg += await self.removeroleifpresent(member, vp)
                            msg += await self.removeroleifpresent(member, pres)'''
                if not rolefound:
                    msg += f"Role for the club {player.club.name} not found."
                msg += await self.addroleifnotpresent(member, labs)
                msg += await self.removeroleifpresent(member, guest)
            elif "club" in player.raw_data and player.club.name not in club and 'LA ' in player.club.name and memberrole is not None: #one club -> another club
                rolefound = False
                for r in ch.guild.roles:
                    if " ".join(r.name.split(' ', 2)[:2]) == player.club.name:
                        rolefound = True
                        msg += await self.addroleifnotpresent(member, r)
                        '''if player.club.role == 'Vice President':
                            msg += await self.addroleifnotpresent(member, vp)
                        elif player.club.role == 'President':
                            msg += await self.addroleifnotpresent(member, pres)
                        elif player.club.role == 'Member' or player.club.role == 'Senior':
                            msg += await self.removeroleifpresent(member, vp)
                            msg += await self.removeroleifpresent(member, pres)'''
                if not rolefound:
                    msg += f"Role for the club {player.club.name} not found."
                msg += await self.removeroleifpresent(member, memberrole)
                '''elif player.club is not None and player.club.name in club and 'LA ' in player.club.name and memberrole is not None:  #pres/vp check
                if player.club.role == 'Vice President':
                    msg += await self.addroleifnotpresent(member, vp)
                elif player.club.role == 'President':
                    msg += await self.addroleifnotpresent(member, pres)
                elif player.club.role == 'Member' or player.club.role == 'Senior':
                    msg += await self.removeroleifpresent(member, vp)
                    msg += await self.removeroleifpresent(member, pres)'''
            if msg != "":
                await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))
        
    @sortroles.before_loop
    async def before_sortroles(self):
        await asyncio.sleep(10)
