import discord
import typing
from .utils import *
import brawlstats
import datetime
import aiohttp
from quickchart import QuickChart
import random
from operator import itemgetter, attrgetter

async def tag_convertor(bot, ctx, member, alt=False):
    if alt:
        if isinstance(member, discord.Member):
            return await bot.get_cog("BrawlStarsCog").config.user(member).alt()
        else:
            return None
    else:
        if isinstance(member, discord.Member):
            return await bot.get_cog("BrawlStarsCog").config.user(member).tag()
        elif member.startswith("#"):
            return member.upper().replace('O', '0')
        else:
            try:
                member = bot.get_user(int(member))
                if member is not None:
                    return await bot.get_cog("BrawlStarsCog").config.user(member).tag()
            except ValueError:
                member = discord.utils.get(ctx.guild.members, name=member)
                if member is not None:
                    return await bot.get_cog("BrawlStarsCog").config.user(member).tag()      
        return None

async def get_profile_embed(bot, ctx, member, alt=False):
    if alt:
        tag = await tag_convertor(bot, ctx, member, alt=True)
        if tag is None:
            return badEmbed("This user has no alt saved! Use [prefix]savealt <tag>")
    else:
        tag = await tag_convertor(bot, ctx, member)
        if tag is None:
            return badEmbed("This user has no tag saved! Use [prefix]save <tag>")
        if tag == "":
            desc = "/p\n/profile @user\n/p discord_name\n/p discord_id\n/p #BSTAG"
            return discord.Embed(title="Invalid argument!", colour=discord.Colour.red(), description=desc)

    bs_cog = bot.get_cog("BrawlStarsCog")
    try:
        player = await bs_cog.ofcbsapi.get_player(tag)

    except brawlstats.errors.NotFoundError:
        return badEmbed("No player with this tag found, try again!")

    except brawlstats.errors.RequestError as e:
        return badEmbed("BS API ERROR: " + str(e))

    except brawlstats.errors.RequestError as e:
        return badEmbed("BS API ERROR: " + str(e))
        
    colour = player.name_color if player.name_color is not None else "0xffffffff"
    embed = discord.Embed(color=discord.Colour.from_rgb(
        int(colour[4:6], 16), int(colour[6:8], 16), int(colour[8:10], 16)))
    player_icon_id = player.raw_data["icon"]["id"]
    if bs_cog.icons is None:
        bs_cog.icons = await bs_cog.starlist_request("https://api.brawlapi.com/v1/icons")
    try:
        player_icon = bs_cog.icons['player'][str(player_icon_id)]['imageUrl2']
    except:
        player_icon = member.avatar_url
    embed.set_author(
        name=f"{player.name} {player.raw_data['tag']}",
        icon_url=player_icon)
    embed.add_field(
        name="Trophies",
        value=f"{get_league_emoji(player.trophies)} {player.trophies}")
    embed.add_field(
        name="Highest Trophies",
        value=f"{get_league_emoji(player.highest_trophies)} {player.highest_trophies}")
    embed.add_field(
        name="Level",
        value=f"<:exp:614517287809974405> {player.exp_level}")
    star_powers = sum([len(x.star_powers) for x in player.brawlers])
    gadgets = sum([len(x['gadgets']) for x in player.raw_data['brawlers']])
    embed.add_field(
        name="Unlocked Brawlers",
        value=f"<:brawlers:614518101983232020> {len(player.brawlers)} <:star_power:729732781638156348> {star_powers} <:gadget:716341776608133130> {gadgets}")
    if "tag" in player.raw_data["club"]:
        try:
            club = await bs_cog.ofcbsapi.get_club(player.club.tag)
            embed.add_field(name="Club", value=f"{bs_cog.get_badge(club.raw_data['badgeId'])} {player.club.name}")
            for m in club.members:
                if m.tag == player.raw_data['tag']:
                    embed.add_field(name="Role", value=f"<:role:614520101621989435> {m.role.capitalize()}")
                    break
        except brawlstats.errors.RequestError:
            embed.add_field(name="Club", value=f"<:bsband:600741378497970177> {player.club.name}")
            embed.add_field(
                name="Role",
                value=f"<:offline:642094554019004416> Error while retrieving role")
    else:
        embed.add_field(
            name="Club",
            value=f"<:noclub:661285120287834122> Not in a club")
    embed.add_field(
        name="3v3 Wins",
        value=f"{get_gamemode_emoji(get_gamemode_id('gemgrab'))} {player.raw_data['3vs3Victories']}")
    embed.add_field(
        name="Showdown Wins",
        value=f"{get_gamemode_emoji(get_gamemode_id('showdown'))} {player.solo_victories} {get_gamemode_emoji(get_gamemode_id('duoshowdown'))} {player.duo_victories}")
    rr_levels = ["-", "Normal", "Hard", "Expert", "Master", "Insane"]
    if player.best_robo_rumble_time > 5:
        rr_level = f"Insane {player.best_robo_rumble_time - 5}"
    else:
        rr_level = rr_levels[player.best_robo_rumble_time]
    embed.add_field(
        name="Best RR Level",
        value=f"{get_gamemode_emoji(get_gamemode_id('roborumble'))} {rr_level}")
    #embed.add_field(
    #    name="Best Time as Big Brawler",
    #    value=f"<:biggame:614517022323245056> {player.best_time_as_big_brawler//60}:{str(player.best_time_as_big_brawler%60).rjust(2, '0')}")
    if "highestPowerPlayPoints" in player.raw_data:
        value = f"{player.raw_data['highestPowerPlayPoints']}"
        embed.add_field(name="Highest PP Points", value=f"<:powertrophies:661266876235513867> {value}")
    reset = reset_trophies(player) - player.trophies
    embed.add_field(
        name="Season Reset",
        value=f"<:bstrophy:552558722770141204> {reset} <:starpoint:661265872891150346> {calculate_starpoints(player)}")
    emo = "<:good:450013422717763609> Qualified" if player.raw_data['isQualifiedFromChampionshipChallenge'] else "<:bad:450013438756782081> Not qualified"
    embed.add_field(name="Championship", value=f"{emo}")
    
    try:
        log = (await bs_cog.ofcbsapi.get_battle_logs(player.raw_data['tag'])).raw_data
        plsolo = None
        plteam = None
        for battle in log:
            if "type" in battle['battle']:
                if battle['battle']['type'] == "soloRanked" and plsolo is None:
                    for play in (battle['battle']['teams'][0]+battle['battle']['teams'][1]):
                        if play['tag'] == player.raw_data['tag']:
                            plsolo = play['brawler']['trophies']
                            break
                if battle['battle']['type'] == "teamRanked" and plteam is None:
                    for play in (battle['battle']['teams'][0]+battle['battle']['teams'][1]):
                        if play['tag'] == player.raw_data['tag']:
                            plteam = play['brawler']['trophies']
                            break
            if plsolo is not None and plteam is not None:
                break
        
        lastsolo = 0
        lastteam = 0
        
        if plsolo is not None:
            await bs_cog.config.user(member).plsolo.set(plsolo)
            await bs_cog.config.user(member).lastsolo.set(int(datetime.datetime.timestamp(datetime.datetime.now())))
        elif isinstance(member, discord.Member):
            lastsolo = await bs_cog.config.user(member).lastsolo()
            if (datetime.datetime.now() - datetime.datetime.fromtimestamp(lastsolo)).days > 0:
                plsolo = await bs_cog.config.user(member).plsolo()

        if plteam is not None:
            await bs_cog.config.user(member).plteam.set(plteam)
            await bs_cog.config.user(member).lastteam.set(int(datetime.datetime.timestamp(datetime.datetime.now())))
        elif isinstance(member, discord.Member):
            lastteam = await bs_cog.config.user(member).lastteam()
            if (datetime.datetime.now() - datetime.datetime.fromtimestamp(lastteam)).days > 0:
                plteam = await bs_cog.config.user(member).plteam()

        if plsolo is not None:
            embed.add_field(name="Current Solo League", value=get_power_league(plsolo))
        if plteam is not None:
            embed.add_field(name="Current Team League", value=get_power_league(plteam))
    except:
        pass
    
    texts = [
        "Check out all your brawlers using /brawlers!", 
        "Want to see your club stats? Try /club!", 
        "Have you seen all our clubs? No? Do /clubs!",
        "You can see stats of other players by typing /p @user.",
        "You can display player's stats by using his tag! /p #TAG",
        "Did you know LA Bot can display CR stats as well? /crp",
        "Check www.laclubs.net to see all our clubs!"
    ]

    if "name" in player.raw_data["club"] and player.raw_data["club"]["name"].startswith("LA "):
        try:
            history_url = "https://localhost/api/history/player?tag=" + player.raw_data['tag'].strip("#")
            data = None
            chart_data = []
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=True)) as session:
                async with session.get(history_url) as resp:
                    data = await resp.json()
            if data is not None and data['status'] == "ok":
                for time, trophies in zip(data['times'][:-20:4]+data['times'][-20::2], data['trophies'][:-20:4]+data['trophies'][-20::2]):
                    chart_data.append("{t:new Date(" + str(time*1000) + "),y:" + str(trophies) + "}")
                chart_data.append("{t:new Date(" + str(int(datetime.datetime.timestamp(datetime.datetime.now())*1000)) + "),y:" + str(player.trophies) + "}")
                qc = QuickChart()
                qc.config = """
                {
                    type: 'line',
                    data: {
                        datasets: [{
                            data : """ + str(chart_data).replace("\'", "") + """,
                            label: "trophies",
                            fill: true,
                            cubicInterpolationMode: 'monotone',
                            borderColor: 'rgba(10, 180, 20, 1)',
                            backgroundColor: 'rgba(10, 180, 20, 0.3)'
                        }]
                    },
                    options: {
                        scales: {
                            xAxes: [{
                                type: 'time',
                                time: {
                                    unit: 'day'
                                },
                                distribution: 'linear'
                            }]
                        },
                        responsive: false,
                        legend: {
                            display: false
                        },
                        tooltips: {
                            mode: 'index',
                            intersect: false
                        },
                        title: {
                            display: true,
                            text: 'TROPHY PROGRESSION',
                            fontStyle: 'bold'
                        },
                        layout: {
                            padding: {
                                left: 5,
                                right: 10,
                                top: 0,
                                bottom: 5
                            }
                        }
                    }
                }
                """
                embed.set_image(url=qc.get_short_url())
        except (aiohttp.client_exceptions.ContentTypeError):
            pass
    embed.set_footer(text=random.choice(texts))
    return embed

async def get_brawlers_embeds(bot, ctx, member):
    tag = await tag_convertor(bot, ctx, member)
    if tag is None or tag == "":
        return [badEmbed("This user has no tag saved! Use [prefix]save <tag>")]

    bs_cog = bot.get_cog("BrawlStarsCog")
    try:
        player = await bs_cog.ofcbsapi.get_player(tag)

    except brawlstats.errors.NotFoundError:
        return [badEmbed("No player with this tag found, try again!")]

    except brawlstats.errors.RequestError as e:
        return [badEmbed("BS API ERROR: " + str(e))]

    except Exception as e:
        return [badEmbed("BS API ERROR: " + str(e))]

    colour = player.name_color if player.name_color is not None else "0xffffffff"

    player_icon_id = player.raw_data["icon"]["id"]
    if bs_cog.icons is None:
        bs_cog.icons = await bs_cog.starlist_request("https://api.brawlapi.com/v1/icons")
    try:
        player_icon = bs_cog.icons['player'][str(player_icon_id)]['imageUrl2']
    except:
        player_icon = member.avatar_url

    brawlers = player.raw_data['brawlers']
    brawlers.sort(key=itemgetter('trophies'), reverse=True)

    embedfields = []
    
    for br in brawlers:
        rank = discord.utils.get(bs_cog.bot.emojis, name=f"rank_{br['rank']}")
        ename = f"{get_brawler_emoji(br['name'])} {br['name'].lower().title()} "
        ename += f"<:pp:664267845336825906> {br['power']}"
        evalue = f"{rank} `{br['trophies']}/{br['highestTrophies']}`\n"
        evalue += f"<:star_power:729732781638156348> `{len(br['starPowers'])}` "
        evalue += f"<:gadget:716341776608133130> `{len(br['gadgets'])}`"
        evalue = evalue.strip()
        embedfields.append([ename, evalue])
    
    embedstosend = []
    for i in range(0, len(embedfields), 15):
        embed = discord.Embed(color=discord.Colour.from_rgb(int(colour[4:6], 16), int(colour[6:8], 16), int(colour[8:10], 16)), title=f"Brawlers ({len(brawlers)}):")
        embed.set_author(name=f"{player.name} {player.raw_data['tag']}", icon_url=player_icon)
        for e in embedfields[i:i + 15]:
            embed.add_field(name=e[0], value=e[1], inline=True)
        embedstosend.append(embed)

    for i in range(len(embedstosend)):
        embedstosend[i].set_footer(text=f"Page {i+1}/{len(embedstosend)}")
    return embedstosend

async def get_single_brawler_embed(bot, ctx, member, brawler):
    tag = await tag_convertor(bot, ctx, member)
    if tag is None or tag == "":
        return badEmbed("This user has no tag saved! Use [prefix]save <tag>")

    bs_cog = bot.get_cog("BrawlStarsCog")

    try:
        player = await bs_cog.ofcbsapi.get_player(tag)
        brawler_data = (await bs_cog.starlist_request("https://api.brawlapi.com/v1/brawlers"))['list']
    except brawlstats.errors.NotFoundError:
        return badEmbed("No player with this tag found, try again!")
    except brawlstats.errors.RequestError as e:
        return badEmbed("BS API ERROR: " + str(e))
    except Exception as e:
        return badEmbed("BS API ERROR: " + str(e))

    if brawler.upper() == "RUFFS":
        brawler = "COLONEL RUFFS"

    unlocked = False
    br = None
    for b in player.raw_data['brawlers']:
        if b['name'] == brawler.upper():
            br = b
            unlocked = True
            break

    data = None
    for b in brawler_data:
        if b['name'].upper() == brawler.upper():
            data = b
            break

    if br is None and data is None:
        return badEmbed(f"No such brawler found! If the brawler's name contains spaces surround it with quotes!")

    colour = player.name_color if player.name_color is not None else "0xffffffff"
    embed = discord.Embed(color=discord.Colour.from_rgb(
        int(colour[4:6], 16), int(colour[6:8], 16), int(colour[8:10], 16)))
    if unlocked:
        embed.set_author(name=f"{player.name}'s {data['name']}", icon_url=data['imageUrl2'])
    else:
        embed.set_author(name=f"{data['name']} (Not unlocked)", icon_url=data['imageUrl2'])
    embed.description = f"<:brawlers:614518101983232020> {data['rarity']['name']}"
    if unlocked:
        rank = discord.utils.get(bs_cog.bot.emojis, name=f"rank_{br['rank']}")
        embed.description += f" {rank} {br.get('trophies')}/{br['highestTrophies']}"
        embed.description += f" <:pp:664267845336825906> {br['power']}"
    embed.description += "\n```" + data['description'] + "```"
    embed.set_footer(text=data['class']['name'])
    starpowers = ""
    gadgets = ""
    for star in data['starPowers']:
        owned = False
        if unlocked:
            for sp in br['starPowers']:
                if star['id'] == sp['id']:
                    owned = True
        emoji = "<:star_power:729732781638156348>" if owned else "<:sp_locked:729751963549302854>"
        starpowers += f"{emoji} {star['name']}\n`{star['description']}`\n"
    embed.add_field(name="Star Powers", value=starpowers if starpowers != "" else "No data available")
    
    for gadget in data['gadgets']:
        owned = False
        if unlocked:
            for ga in br['gadgets']:
                if gadget['id'] == ga['id']:
                    owned = True
        emoji = "<:gadget:716341776608133130>" if owned else "<:ga_locked:729752493793476759>"
        gadgets += f"{emoji} {gadget['name']}\n`{gadget['description']}`\n"
    embed.add_field(name="Gadgets", value=gadgets if gadgets != "" else "No data available")
    return embed
