import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.embed import randomize_colour
from redbot.core.utils.menus import menu, prev_page, next_page
from discord.ext import tasks
from random import choice
import asyncio
import brawlstats
from typing import Union
from re import sub

class BrawlStarsCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=5245652)
        default_user = {"tag" : None}
        self.config.register_user(**default_user)
        default_guild = {"clubs" : {}}
        self.config.register_guild(**default_guild)
        self.sortroles.start()
        
    def cog_unload(self):
        self.sortroles.cancel()
        
    async def initialize(self):
        bsapikey = await self.bot.get_shared_api_tokens("bsapi")
        if bsapikey["api_key"] is None:
            raise ValueError("The Brawl Stars API key has not been set.")
        self.bsapi = brawlstats.BrawlAPI(bsapikey["api_key"], is_async=True, prevent_ratelimit=True)
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set.")
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

    def get_rank_emoji(self, rank : int):
        if 1 <= rank < 5:
            return "<:rank1:664262410265165824>"
        elif 5 <= rank < 10:
            return "<:rank5:664262466812772377>"
        elif 10 <= rank < 15:
            return "<:rank10:664262501344608257>"
        elif 15 <= rank < 20:
            return "<:rank15:664262551139254312>"
        elif 20 <= rank < 25:
            return "<:rank20:664262586266681371>"
        elif 25 <= rank < 30:
            return "<:rank25:664262630223118357> "
        elif 30 <= rank < 35:
            return "<:rank30:664262657557397536>"
        elif 35 <= rank:
            return "<:rank35:664262686028333056>"

    def get_brawler_emoji(self, name : str):
        if name == "SHELLY":
            return "<:shelly:664235199076237323>"
        elif name == "TICK":
            return "<:tick:664235450889928744>"
        elif name == "TARA":
            return "<:tara:664236127015796764>"
        elif name == "SPIKE":
            return "<:spike:664235867748958249>"
        elif name == "SANDY":
            return "<:sandy:664235310573420544>"
        elif name == "ROSA":
            return "<:rosa:664235409722834954>"
        elif name == "RICO":
            return "<:rico:664235890171707393>"
        elif name == "EL PRIMO":
            return "<:primo:664235742758830135>"
        elif name == "POCO":
            return "<:poco:664235668393689099>"
        elif name == "PIPER":
            return "<:piper:664235622998867971>"
        elif name == "PENNY":
            return "<:penny:664235535094644737>"
        elif name == "PAM":
            return "<:pam:664235599804235786>"
        elif name == "NITA":
            return "<:nita:664235795959513088>"
        elif name == "MORTIS":
            return "<:mortis:664235717693800468>"
        elif name == "MAX":
            return "<:max:664235224762155073>"
        elif name == "LEON":
            return "<:leon:664235430530514964>"
        elif name == "JESSIE":
            return "<:jessie:664235816339636244>"
        elif name == "GENE":
            return "<:gene:664235476084981795>"
        elif name == "FRANK":
            return "<:frank:664235513242320922>"
        elif name == "EMZ":
            return "<:emz:664235245956235287>"
        elif name == "DYNAMIKE":
            return "<:dynamike:664235766620094464>"
        elif name == "DARRYL":
            return "<:darryl:664235555877290008>"
        elif name == "CROW":
            return "<:crow:664235693064716291>"
        elif name == "COLT":
            return "<:colt:664235956202766346>"
        elif name == "CARL":
            return "<:carl:664235388537274369>"
        elif name == "BULL":
            return "<:bull:664235934006378509>"
        elif name == "BROCK":
            return "<:brock:664235912150122499>"
        elif name == "BO":
            return "<:bo:664235645287530528>"
        elif name == "BIBI":
            return "<:bibi:664235367615954964>"
        elif name == "BEA":
            return "<:bea:664235276758941701>"
        elif name == "BARLEY":
            return "<:barley:664235839316033536>"
        elif name == "8-BIT":
            return "<:8bit:664235332522213418>"
        elif name == "MR. P":
            return "<:mrp:671379771585855508>"
        
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
        elif member.startswith("#"):
            tag = member.upper().replace('O', '0')
        else:
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

        colour = player.name_color if player.name_color is not None else "0xffffffff"
        embed=discord.Embed(color=discord.Colour.from_rgb(int(colour[4:6], 16), int(colour[6:8], 16), int(colour[8:10], 16)))
        embed.set_author(name=f"{player.name} {player.raw_data['tag']}", icon_url=member.avatar_url if isinstance(member, discord.Member) else "https://i.imgur.com/ZwIP41S.png")
        embed.add_field(name="Trophies", value=f"{self.get_league_emoji(player.trophies)} {player.trophies}")
        embed.add_field(name="Highest Trophies", value=f"<:totaltrophies:614517396111097866> {player.highest_trophies}")
        embed.add_field(name="Level", value=f"<:exp:614517287809974405> {player.exp_level}")
        embed.add_field(name="Unlocked Brawlers", value=f"<:brawlers:614518101983232020> {len(player.brawlers)}")
        if "tag" in player.raw_data["club"]:
            embed.add_field(name="Club", value=f"<:bsband:600741378497970177> {player.club.name}")
            try:
                club = await player.get_club()
                for m in club.members:
                    if m.tag == player.raw_data['tag']:
                        embed.add_field(name="Role", value=f"<:role:614520101621989435> {m.role.capitalize()}")
                        break
            except brawlstats.errors.RequestError:
                embed.add_field(name="Role", value=f"<:offline:642094554019004416> Error while retrieving role")
        else:
            embed.add_field(name="Club", value=f"<:noclub:661285120287834122> Not in a club")
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

    @commands.command(aliases=['b'])
    async def brawlers(self, ctx, *, member: Union[discord.Member, str] = None):
        """Brawl Stars brawlers"""
        await ctx.trigger_typing()
        prefix = ctx.prefix
        tag = ""

        member = ctx.author if member is None else member

        if isinstance(member, discord.Member):
            tag = await self.config.user(member).tag()
            if tag is None:
                return await ctx.send(embed=self.badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))
        elif member.startswith("#"):
            tag = member.upper().replace('O', '0')
        else:
            try:
                member = discord.utils.get(ctx.guild.members, id=int(member))
                if member is not None:
                    tag = await self.config.user(member).tag()
                    if tag is None:
                        return await ctx.send(
                            embed=self.badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))
            except ValueError:
                member = discord.utils.get(ctx.guild.members, name=member)
                if member is not None:
                    tag = await self.config.user(member).tag()
                    if tag is None:
                        return await ctx.send(
                            embed=self.badEmbed(f"This user has no tag saved! Use {prefix}bssave <tag>"))

        if tag is None or tag == "":
            desc = "/p\n/bsprofile @user\n/p discord_name\n/p discord_id\n/p #CRTAG"
            embed = discord.Embed(title="Invalid argument!", colour=discord.Colour.red(), description=desc)
            return await ctx.send(embed=embed)
        try:
            player = await self.ofcbsapi.get_player(tag)

        except brawlstats.errors.NotFoundError:
            return await ctx.send(embed=self.badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed=self.badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send(
                "****Something went wrong, please send a personal message to LA Modmail bot or try again!****")

        colour = player.name_color if player.name_color is not None else "0xffffffff"

        brawlers = []
        messages = []
        for brawler in player.raw_data['brawlers']:
            pair = []
            pair.append(brawler.get('name'))
            pair.append(brawler.get('trophies'))
            brawlers.append(pair)
        brawlers = sorted(brawlers, key=lambda x: x[1], reverse=True)
        brawlersmsg = ""
        for brawler in brawlers:
            if len(brawlersmsg) > 900:
                messages.append(brawlersmsg)
                brawlersmsg = ""
            brawlersmsg += (f"{self.get_brawler_emoji(brawler[0])} **{brawler[0].lower().capitalize()}**: {brawler[1]} <:bstrophy:552558722770141204>\n")
        if len(brawlersmsg) > 0:
            messages.append(brawlersmsg)
        for m in messages:
            embed = discord.Embed(
                color=discord.Colour.from_rgb(int(colour[4:6], 16), int(colour[6:8], 16), int(colour[8:10], 16)))
            embed.set_author(name=f"{player.name} {player.raw_data['tag']}", icon_url=member.avatar_url if isinstance(member, discord.Member) else "https://i.imgur.com/ZwIP41S.png")
            embed.add_field(name=f"**Brawlers({len(brawlers)}\\33):**", value=m)
            await ctx.send(embed=embed)

    @commands.command()
    async def brawler(self, ctx, brawler : str, member: discord.Member = None):
        """Brawler specific info"""
        await ctx.trigger_typing()
        prefix = ctx.prefix

        if member == None:
            member = ctx.author

        tag = await self.config.user(member).tag()
        if tag is None:
            return await ctx.send(embed=self.badEmbed(f"You have no tag saved! Use {prefix}bssave <tag>"))

        if tag is None or tag == "":
            desc = "/p\n/bsprofile @user\n/p discord_name\n/p discord_id\n/p #CRTAG"
            embed = discord.Embed(title="Invalid argument!", colour=discord.Colour.red(), description=desc)
            return await ctx.send(embed=embed)
        try:
            player = await self.ofcbsapi.get_player(tag)

        except brawlstats.errors.NotFoundError:
            return await ctx.send(embed=self.badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed=self.badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        except Exception as e:
            return await ctx.send(
                "****Something went wrong, please send a personal message to LA Modmail bot or try again!****")

        br = None
        for b in player.raw_data['brawlers']:
            if b.get('name') == brawler.upper():
                br = b
        if br is None:
            return await ctx.send(embed=self.badEmbed(f"There's no such brawler!"))

        colour = player.name_color if player.name_color is not None else "0xffffffff"
        embed = discord.Embed(
            color=discord.Colour.from_rgb(int(colour[4:6], 16), int(colour[6:8], 16), int(colour[8:10], 16)))
        embed.set_author(name=f"{player.name} {player.raw_data['tag']}", icon_url=member.avatar_url if isinstance(member, discord.Member) else "https://i.imgur.com/ZwIP41S.png")
        embed.add_field(name="Brawler", value=f"{self.get_brawler_emoji(brawler.upper())} {brawler.lower().capitalize()}")
        embed.add_field(name="Trophies", value=f"<:bstrophy:552558722770141204> {br.get('trophies')}")
        embed.add_field(name="Highest Trophies", value=f"{self.get_rank_emoji(br.get('rank'))} {br.get('highestTrophies')}")
        embed.add_field(name="Power Level", value=f"<:pp:664267845336825906> {br.get('power')}")
        starpowers = ""
        for star in br.get('starPowers'):
            starpowers += f"<:starpower:664267686720700456> {star.get('name')}\n"
        if starpowers != "":
            embed.add_field(name="Star Powers", value=starpowers)
        else:
            embed.add_field(name="Star Powers", value="<:starpower:664267686720700456> None")
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
        elif key.startswith("#"):
            tag = key.upper().replace('O', '0')
        else:
            tag = await self.config.guild(ctx.guild).clubs.get_raw(key.lower(), "tag", default=None)
            if tag is None:
                return await ctx.send(embed = self.badEmbed(f"{key.title()} isn't saved club in this server!"))
        try:
            club = await self.ofcbsapi.get_club(tag)
                        
        except brawlstats.errors.NotFoundError:
            return await ctx.send(embed = self.badEmbed("No club with this tag found, try again!"))
        
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
                await menu(ctx, embedsToSend, {"⬅": prev_page, "➡": next_page,} , timeout=2000)
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

    async def removeroleifpresent(self, member: discord.Member, *roles):
        msg = ""
        for role in roles:
            if role in member.roles:
                await member.remove_roles(role)
                msg += f"Removed **{str(role)}** from **{str(member)}**\n"
        return msg

    async def addroleifnotpresent(self, member: discord.Member, *roles):
        msg = ""
        for role in roles:
            if role not in member.roles:
                await member.add_roles(role)
                msg += f"Added **{str(role)}** to **{str(member)}**\n"
        return msg
            
    @tasks.loop(hours=4)
    async def sortroles(self):
        ch = self.bot.get_channel(653295573872672810)
        await ch.trigger_typing()
        labs = ch.guild.get_role(576028728052809728)
        guest = ch.guild.get_role(578260960981286923)
        newcomer = ch.guild.get_role(534461445656543255)
        brawlstars = ch.guild.get_role(576002604740378629)
        vp = ch.guild.get_role(536993652648574976)
        pres = ch.guild.get_role(536993632918568991)
        error_counter = 0
        
        for member in ch.guild.members:
            if member.bot:
                continue
            tag = await self.config.user(member).tag()
            if tag is None:
                continue      
            try:
                player = await self.ofcbsapi.get_player(tag)
                await asyncio.sleep(0.1)
            except brawlstats.errors.RequestError as e:
                error_counter += 1
                if error_counter == 5:
                    await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=f"Stopping after 5 request errors! Displaying the last one:\n({str(e)})"))
                    break
                continue
            except Exception as e:
                return await ch.send(embed=discord.Embed(colour=discord.Colour.red(), description=f"**Something went wrong while requesting {tag}!**\n({str(e)})"))           
                continue
                        
            msg = ""            
            player_in_club = "name" in player.raw_data["club"]
            member_roles = []
            member_role = None                   
            member_role_expected = None
                        
            for role in member.roles:
                if role.name.startswith('LA '):
                    member_roles.append(role)
                        
            if len(member_roles) > 1:
                msg += f"**{str(member)}** has more than one club role. Removing **{', '.join([str(r) for r in member_roles])}**"
                for role in member_roles:
                    await self.removeroleifpresent(member, role)
            elif len(member_roles) == 1:
                member_role = member_roles[0]

            if not player_in_club:
                msg += await self.removeroleifpresent(member, labs, vp, pres, newcomer)
                msg += await self.addroleifnotpresent(member, guest)
                if member_role is not None:
                    msg += await self.removeroleifpresent(member, member_role)
                
            if player_in_club and "LA " not in player.club.name:
                msg += await self.removeroleifpresent(member, labs, vp, pres, newcomer)
                msg += await self.addroleifnotpresent(member, guest, brawlstars)

            if player_in_club and "LA " in player.club.name:
                for role in ch.guild.roles:
                    if sub(r'[^\x00-\x7f]',r'', role.name).strip() == player.club.name:
                        member_role_expected = role
                        break
                if member_role_expected is None:
                    await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=f"Role for the club {player.club.name} not found. Input: {player.club.name}.\n"))
                    continue
                msg += await self.removeroleifpresent(member, guest, newcomer)
                msg += await self.addroleifnotpresent(member, labs, brawlstars)
                if member_role is None:
                    msg += await self.addroleifnotpresent(member, member_role_expected)
                elif member_role != member_role_expected:
                    msg += await self.removeroleifpresent(member, member_role)
                    msg += await self.addroleifnotpresent(member, member_role_expected)
                player_club = await player.get_club()
                for mem in player_club.members:
                    if mem.tag == player.raw_data['tag']:
                        if mem.role.lower() == 'vicepresident':
                            msg += await self.addroleifnotpresent(member, vp)
                            msg += await self.removeroleifpresent(member, pres)
                        elif mem.role.lower() == 'president':
                            msg += await self.addroleifnotpresent(member, pres)
                            msg += await self.removeroleifpresent(member, vp)
                        elif mem.role.lower() == 'member':
                            msg += await self.removeroleifpresent(member, vp, pres)
                        break

            if msg != "":
                await ch.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))

    @sortroles.before_loop
    async def before_sortroles(self):
        await asyncio.sleep(5)

    @commands.command()
    @commands.guild_only()
    async def newcomer(self, ctx, tag, member : discord.Member):
        if ctx.guild.id != 401883208511389716:
            return await ctx.send("This command can't be used in this server.")

        mod = ctx.guild.get_role(520719415109746690)
        roles = ctx.guild.get_role(564552111875162112)

        if mod not in ctx.author.roles and roles not in ctx.author.roles and not ctx.author.guild_permissions.administrator:
            return await ctx.send("You can't use this command.")

        await ctx.trigger_typing()

        labs = ctx.guild.get_role(576028728052809728)
        guest = ctx.guild.get_role(578260960981286923)
        newcomer = ctx.guild.get_role(534461445656543255)
        brawlstars = ctx.guild.get_role(576002604740378629)
        vp = ctx.guild.get_role(536993652648574976)
        pres = ctx.guild.get_role(536993632918568991)
        es = ctx.guild.get_role(548557736120418313)
        hr = ctx.guild.get_role(564213036257247234)
        fi = ctx.guild.get_role(608436019469090817)
        hi = ctx.guild.get_role(610351625113960469)
        pl = ctx.guild.get_role(576148906602397717)

        tag = tag.lower().replace('O', '0')
        if tag.startswith("#"):
            tag = tag.strip('#')

        msg = ""
        try:
            player = await self.ofcbsapi.get_player(tag)
            await self.config.user(member).tag.set(tag.replace("#", ""))
            msg += "BS account **{}** was saved to **{}**\n".format(player.name, member.name)

        except brawlstats.errors.NotFoundError:
            await ctx.send(embed=self.badEmbed("No player with this tag found!"))
            return

        except brawlstats.errors.RequestError as e:
            await ctx.send(embed=self.badEmbed(f"BS API is offline, please try again later! ({str(e)})"))
            return

        except Exception as e:
            await ctx.send(
                "**Something went wrong, please send a personal message to LA Modmail bot or try again!****")
            return

        nick = f"{player.name}"
        try:
            await member.edit(nick=nick[:31])
            msg += f"New nickname: **{nick[:31]}**\n"
        except discord.Forbidden:
            msg += f"I dont have permission to change nickname of this user!\n"
        except Exception as e:
            await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=f"Something went wrong: {str(e)}"))
            return

        player_in_club = "name" in player.raw_data["club"]
        member_role_expected = None

        if not player_in_club:
            msg += await self.removeroleifpresent(member, newcomer)
            msg += await self.addroleifnotpresent(member, guest, brawlstars)

        if player_in_club and "LA " not in player.club.name:
            msg += await self.removeroleifpresent(member, newcomer)
            msg += await self.addroleifnotpresent(member, guest, brawlstars)

        if player_in_club and "LA " in player.club.name:
            for role in ctx.guild.roles:
                if sub(r'[^\x00-\x7f]', r'', role.name).strip() == player.club.name:
                    member_role_expected = role
                    if "🇪🇸" in str(role):
                        msg += await self.addroleifnotpresent(member, es)
                    elif "🇭🇷" in str(role):
                        msg += await self.addroleifnotpresent(member, hr)
                    elif "🇫🇮" in str(role):
                        msg += await self.addroleifnotpresent(member, fi)
                    elif "🇮🇳" in str(role):
                        msg += await self.addroleifnotpresent(member, hi)
                    elif "🇵🇱" in str(role):
                        msg += await self.addroleifnotpresent(member, pl)
                    break
            if member_role_expected is None:
                await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=f"Role for the club {player.club.name} not found. Input: {club_name}.\n"))
                return
            msg += await self.removeroleifpresent(member, newcomer)
            msg += await self.addroleifnotpresent(member, labs, brawlstars)
            msg += await self.addroleifnotpresent(member, member_role_expected)
            try:
                player_club = await player.get_club()
                for mem in player_club.members:
                    if mem.tag == player.raw_data['tag']:
                        if mem.role.lower() == 'vicepresident':
                            msg += await self.addroleifnotpresent(member, vp)
                        elif mem.role.lower() == 'president':
                            msg += await self.addroleifnotpresent(member, pres)
                        break
            except brawlstats.errors.RequestError:
                msg += "<:offline:642094554019004416> Couldn't retrieve player's club role."
        if msg != "":
            await ctx.send(embed=discord.Embed(colour=discord.Colour.blue(), description=msg))
