import datetime
import typing
from operator import attrgetter, itemgetter

import discord
from fuzzywuzzy import process

from .utils import *


async def get_event_embeds(bot):
    bs_cog = bot.get_cog("BrawlStarsCog")
    events = await bs_cog.starlist_request("https://api.brawlapi.com/v1/events")
    if 'status' in events:
        return [badEmbed(f"Something went wrong. Please try again later!")]
    time_now = datetime.datetime.now()
    embed1 = discord.Embed(title="ACTIVE EVENTS",
                           colour=discord.Colour.green())
    embed2 = discord.Embed(title="UPCOMING EVENTS",
                           colour=discord.Colour.green())
    active = ""
    for ev in events['active']:
        if ev['slot']['name'] == "Duo Showdown":
            continue
        modifier = ""
        powerplay = ""
        if ev['slot']['name'] == "Power Play":
            powerplay = "<:powertrophies:661266876235513867> "
        if ev['modifier'] is not None:
            modifier = f"↳ Modifier: {ev['modifier']['name']}\n"
        active += f"**{powerplay}{get_gamemode_emoji(ev['map']['gameMode']['id'])} {ev['map']['gameMode']['name']}**\n↳ Map: {ev['map']['name']}\n{modifier}"
    embed1.description = active
    upcoming = ""
    for ev in events['upcoming']:
        if ev['slot']['name'] == "Duo Showdown":
            continue
        modifier = ""
        powerplay = ""
        challenge = ""
        if ev['slot']['name'] == "Power Play":
            powerplay = "<:powertrophies:661266876235513867> "
        if "challenge" in ev['slot']['name'].lower():
            challenge = "<:totaltrophies:614517396111097866> "
        if ev['modifier'] is not None:
            modifier = f"↳ Modifier: {ev['modifier']['name']}\n"
        start = datetime.datetime.strptime(
            ev['startTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        diff = time_left((start - time_now).total_seconds())
        upcoming += f"**{challenge}{powerplay}{get_gamemode_emoji(ev['map']['gameMode']['id'])} {ev['map']['gameMode']['name']}**\n↳ Map: {ev['map']['name']}\n↳ Starts in: {diff}\n{modifier}"
    embed2.description = upcoming
    embed2.set_footer(text="Data provided by brawlify.com")
    return [embed1, embed2]


async def get_map_embed(bot, map_name):
    bs_cog = bot.get_cog("BrawlStarsCog")
    if bs_cog.maps is None:
        final = {}
        all_maps = await bs_cog.starlist_request("https://api.brawlapi.com/v1/maps")
        for m in all_maps['list']:
            hash_ = m['hash'] + "-old" if m['disabled'] else m['hash']
            hash_ = ''.join(i for i in hash_ if not i.isdigit())
            final[hash_] = {'url': m['imageUrl'], 'name': m['name'],
                            'disabled': m['disabled'], 'link': m['link'],
                            'gm_url': m['gameMode']['imageUrl'], 'id': m['id']}
        bs_cog.maps = final

    map_name = map_name.replace(" ", "-")
    result = process.extract(map_name, list(bs_cog.maps.keys()), limit=1)
    result_map = bs_cog.maps[result[0][0]]
    embed = discord.Embed(colour=discord.Colour.green())
    embed.set_author(
        name=result_map['name'], url=result_map['link'], icon_url=result_map['gm_url'])
    data = (await bs_cog.starlist_request(f"https://api.brawlapi.com/v1/maps/{result_map['id']}/600+"))
    brawlers = (await bs_cog.starlist_request(f"https://api.brawlapi.com/v1/brawlers"))['list']
    if 'stats' in data and len(data['stats']) > 0:
        stats = data['stats']
        if len(stats) > 0 and 'winRate' in stats[0]:
            wr = ""
            stats.sort(key=itemgetter('winRate'), reverse=True)
            for counter, br in enumerate(stats[:10], start=1):
                id = None
                for b in brawlers:
                    if b['id'] == br['brawler']:
                        id = b['id']
                        break
                if id is None:
                    continue
                wr += f"{get_brawler_emoji(bot, id)} `{int(br['winRate'])}%` "
                if counter % 5 == 0:
                    wr += "\n"
            if wr.strip() != "":
                embed.add_field(name="Best Win Rates", value=wr, inline=False)

        if len(stats) > 0 and 'bossWinRate' in stats[0]:
            bwr = ""
            stats.sort(key=itemgetter('bossWinRate'), reverse=True)
            for counter, br in enumerate(stats[:10], start=1):
                id = None
                for b in brawlers:
                    if b['id'] == br['brawler']:
                        id = b['id']
                        break
                if id is None:
                    continue
                bwr += f"{get_brawler_emoji(bot, id)} `{int(br['bossWinRate'])}%` "
                if counter % 5 == 0:
                    bwr += "\n"
            if wr.strip() != "":
                embed.add_field(name="Best Boss Win Rates",
                                value=bwr, inline=False)

        if len(stats) > 0 and 'useRate' in stats[0]:
            ur = ""
            stats.sort(key=itemgetter('useRate'), reverse=True)
            for counter, br in enumerate(stats[:10], start=1):
                id = None
                for b in brawlers:
                    if b['id'] == br['brawler']:
                        id = b['id']
                        break
                if id is None:
                    continue
                ur += f"{get_brawler_emoji(bot, id)} `{int(br['useRate'])}%` "
                if counter % 5 == 0:
                    ur += "\n"
            if wr.strip() != "":
                embed.add_field(name="Highest Use Rates",
                                value=ur, inline=False)

    if result_map['disabled']:
        embed.description = "This map is currently disabled."
    embed.set_footer(text="Data provided by brawlify.com")
    embed.set_image(url=result_map['url'])
    return embed
