import discord
import typing
from .utils import *
import datetime

async def get_event_embeds(bot):
    bs_cog = bot.get_cog("BrawlStarsCog")
    events = await bs_cog.starlist_request("https://api.brawlapi.com/v1/events")
    if 'status' in events:
        return [badEmbed(f"Something went wrong. Please try again later!")]
    time_now = datetime.datetime.now()
    embed1 = discord.Embed(title="ACTIVE EVENTS", colour=discord.Colour.green())
    embed2 = discord.Embed(title="UPCOMING EVENTS", colour=discord.Colour.green())
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
        start = datetime.datetime.strptime(ev['startTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        diff = time_left((start - time_now).total_seconds())
        upcoming += f"**{challenge}{powerplay}{get_gamemode_emoji(ev['map']['gameMode']['id'])} {ev['map']['gameMode']['name']}**\n↳ Map: {ev['map']['name']}\n↳ Starts in: {diff}\n{modifier}"
    embed2.description = upcoming
    embed2.set_footer(text="Data provided by brawlify.com")
    return [embed1, embed2]