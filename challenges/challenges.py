import discord
from discord.ext import tasks
from redbot.core import commands, Config, checks
from redbot.core.data_manager import cog_data_path

import brawlstats
import asyncio
from datetime import datetime as dt
from datetime import timedelta
import json
import traceback
import textwrap

class Challenges(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=25202025)
        default_member = {"tokens" : 0}
        default_server = {"active_challenges" : {}, "channel" : None, "log": None}
        self.config.register_member(**default_member)
        self.config.register_global(**default_server)
        self.labs = 401883208511389716
        self.bsconfig = None
        with open(str(cog_data_path(self)).replace("Challenges", r"CogManager/cogs/challenges/challenge_data.json")) as file:
            self.challenge_data = json.load(file)
        self.token = " token"#"🪙"
        self.loading = {
            "empty": ["<:blankleft:821065351907246201>", "<:blankmid:821065351294615552>", "<:blankright:821065351621115914>"],
            "full": ["<:loadleft:821065351726366761>", "<:loadmid:821065352061780048>", "<:loadright:821065351903182889>"]
        }
        self.challenge_update_loop.start()
        self.progress_update_loop.start()

    def cog_unload(self):
        self.challenge_update_loop.stop()
        self.progress_update_loop.stop()

    async def initialize(self):
        ofcbsapikey = await self.bot.get_shared_api_tokens("ofcbsapi")
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set.")
        self.ofcbsapi = brawlstats.Client(
            ofcbsapikey["api_key"], is_async=True)

    def get_bs_config(self):
        if self.bsconfig is None:
            self.bsconfig = Config.get_conf(None, identifier=5245652, cog_name="BrawlStarsCog")
        return self.bsconfig

    def labs_check(self, guild: discord.Guild):
        return guild.id == self.labs

    def time_left(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if hours <= 24:
            return "{}h {:02}m".format(int(hours), int(minutes))
        else:
            return f"{int(hours)//24}d {(int(hours)//24)%24}h"

    @tasks.loop(minutes=3)
    async def challenge_update_loop(self):
        labs = self.bot.get_guild(self.labs)
        labs_channel_id = await self.config.guild(labs).channel()
        labs_log_id = await self.config.guild(labs).log()
        if labs_channel_id is None or labs_log_id is None:
            return
        labs_channel = labs.get_channel(labs_channel_id)
        log_channel = labs.get_channel(labs_log_id)
        labs_challs = await self.config.guild(labs).active_challenges()
        if labs_challs is None:
            await self.config.guild(labs).set_raw("active_challenges", value={})
            labs_challs = {}
        now = dt.now()

        #prepare challenges 24h in advance
        for chal_id in self.challenge_data:
            start_date = dt.strptime(self.challenge_data[chal_id]["start"], "%d/%m/%y %H:%M")
            end_date = dt.strptime(self.challenge_data[chal_id]["end"], "%d/%m/%y %H:%M")
            if chal_id not in labs_challs.keys() and ((start_date - now) < timedelta(hours=24)) and (now < end_date):
                await self.log(log_channel, f"Setting up upcoming {chal_id}", discord.Color.orange())
                data = self.challenge_data[chal_id].copy()
                data["status"] = "start_soon"
                embed = self.make_chall_embed(data, chal_id)
                message = await labs_channel.send(embed=embed)
                data["embed"] = embed.to_dict()
                data["message_id"] = message.id
                data["participants"] = {}
                labs_challs[chal_id] = data
                await self.config.guild(labs).set_raw("active_challenges", chal_id, value=data)
        #update prepared and handle status changes
        for chal_id in labs_challs:
            data = labs_challs[chal_id]
            if data["status"] == "start_soon":
                start_date = dt.strptime(data["start"], "%d/%m/%y %H:%M")
                if (start_date - now) < timedelta(hours=24):
                    starts = self.time_left((start_date - now).total_seconds())
                    message = labs_channel.get_partial_message(data["message_id"])
                    embed = discord.Embed.from_dict(data["embed"])
                    embed.set_field_at(0, name="Starts in", value=starts)
                    await message.edit(embed=embed)
                if now >= start_date:
                    await self.log(log_channel, f"Starting {chal_id}", discord.Color.orange())
                    data["status"] = "active"
                    ends = self.time_left((dt.strptime(data["end"], "%d/%m/%y %H:%M") - now).total_seconds())
                    message = labs_channel.get_partial_message(data["message_id"])
                    embed = discord.Embed.from_dict(data["embed"])
                    embed.set_field_at(0, name="Time left", value=ends)
                    embed.description = embed.description + "\nCheck your progress with `/ch stats`"
                    if 'global' in data:
                        glob_pro= f"0/{data['global']['goal']}\n" + self.loading['empty'][0] + self.loading['empty'][1]*8 + self.loading['empty'][2]
                        embed.add_field(name="Progress", value=glob_pro, inline=False)
                    participants = data["participants"]
                    embed.set_footer(text="Participants: " + str(len(participants.keys())))
                    data["embed"] = embed.to_dict()
                    await message.edit(embed=embed)
                    await self.config.guild(labs).set_raw("active_challenges", chal_id, "status", value="active")
                    await self.config.guild(labs).set_raw("active_challenges", chal_id, "embed", value=embed.to_dict())
            if data["status"] == "active":
                #score update is independent loop

                end_date = dt.strptime(data["end"], "%d/%m/%y %H:%M")
                if now >= end_date:
                    await self.log(log_channel, f"Marking {chal_id} as ended", discord.Color.purple())
                    data["status"] = "to_be_ended"
                    message = labs_channel.get_partial_message(data["message_id"])
                    embed = discord.Embed.from_dict(data["embed"])
                    embed.set_field_at(0, name="Time left", value="Ending soon...")
                    await message.edit(embed=embed)
                    await self.config.guild(labs).set_raw("active_challenges", chal_id, "status", value="to_be_ended")
                else:
                    message = labs_channel.get_partial_message(data["message_id"])
                    embed = discord.Embed.from_dict(data["embed"])
                    ends = self.time_left((end_date - now).total_seconds())
                    embed.set_field_at(0, name="Time left", value=ends)

                    participants = data["participants"]
                    if 'global' in data:
                        total = sum([participants["progress"] for id in participants])
                        percentage = int((total/data['global']['goal'])*100)
                        first = self.loading['empty'][0] if percentage < 10 else self.loading['full'][0]
                        full = int((percentage-10)/10)
                        if full < 0:
                            full = 0
                        if full > 8:
                            full = 8
                        middle = self.loading['full'][1] * full + self.loading['empty'][1] * (8 - full)
                        last = self.loading['empty'][2] if percentage < 100 else self.loading['full'][2]
                        glob_pro = f"{total}/{data['global']['goal']}\n" + first + middle + last
                        embed.set_field_at(2, name="Progress", value=glob_pro, inline=False)
                    embed.set_footer(text="Participants: " + str(len(participants.keys())))
                    await message.edit(embed=embed)
                    data["embed"] = embed.to_dict()
                    await self.config.guild(labs).set_raw("active_challenges", chal_id, "embed", value=embed.to_dict())

            if data["status"] == "to_be_ended":
                await self.log(log_channel, f"Finishing {chal_id}", discord.Color.purple())
                await self.challenge_finish()

                await self.log(log_channel, f"Ending {chal_id}", discord.Color.purple())
                data["status"] = "ended"
                message = labs_channel.get_partial_message(data["message_id"])
                embed = discord.Embed.from_dict(data["embed"])
                embed.remove_field(0)
                embed.title = "[ENDED] " + data["name"]
                embed.description = data["description"] + "\nCheck your progress with `/ch stats`"
                data["embed"] = embed.to_dict()
                await message.edit(embed=embed)
                await self.config.guild(labs).set_raw("active_challenges", chal_id, "status", value="ended")
                await self.config.guild(labs).set_raw("active_challenges", chal_id, "embed", value=embed.to_dict())

            if data["status"] == "ended":
                end_date = dt.strptime(data["end"], "%d/%m/%y %H:%M")
                if (now - end_date) > timedelta(hours=1): ###DEBUG!!!!CHANGE BACK TO 24
                    await self.log(log_channel, f"Deleting {chal_id}", discord.Color.purple())
                    message = labs_channel.get_partial_message(data["message_id"])
                    await message.delete()
                    await self.config.guild(labs).clear_raw("active_challenges", chal_id)
        
    @challenge_update_loop.error
    async def challenge_update_loop_errors(self, error):
        await self.log_error(error)

    @tasks.loop(minutes=3)
    async def progress_update_loop(self):
        labs = self.bot.get_guild(self.labs)
        labs_channel_id = await self.config.guild(labs).channel()
        labs_log_id = await self.config.guild(labs).log()
        if labs_channel_id is None or labs_log_id is None:
            return
        labs_channel = labs.get_channel(labs_channel_id)
        log_channel = labs.get_channel(labs_log_id)
        labs_challs = await self.config.guild(labs).active_challenges()
        if labs_challs is None:
            await self.config.guild(labs).set_raw("active_challenges", value={})
            labs_challs = {}
        now = dt.now()
        bs_conf = self.get_bs_config()
        tags = await bs_conf.all_users()
        
        for chall_id in labs_challs:
            if labs_challs[chall_id]["status"] == "active":
                data = labs_challs[chall_id]
                participants = data["participants"]
                gamemodes = data["gamemodes"]
                brawlers = data["brawlers"]
                type = data["type"]
                min_trophy = data["min_trophy"]

                score = 0

                for mem_id in participants:
                    last = participants[str(mem_id)]["last"]
                    user = labs.get_member(mem_id)
                    if user is None:
                        continue
                    tag = tags[user.id]['tag'].replace("o", "0").replace("O", "0")
                    try:
                        log = await self.ofcbsapi.get_battle_logs(tag)
                        await asyncio.sleep(0.03)
                        log = log.raw_data
                    except brawlstats.errors.RequestError as e:
                        await self.log_error(e)
                        break
                    except Exception as e:
                        await self.log_error(e)
                        break
                    for battle in log:
                        b_time = dt.strptime(battle['battleTime'], '%Y%m%dT%H%M%S.%fZ')
                        if b_time <= dt.strptime(last, '%Y%m%dT%H%M%S.%fZ'):
                            break
                        
                        if "id" in battle['event'] and battle['event']['id'] == 0 and ("type" not in battle['battle'] or battle['battle']['type'] != "ranked"):
                            continue
                        if "type" in battle['battle'] and battle['battle']['type'] == "friendly":
                            continue
                        
                        if len(gamemodes) > 0 and battle['battle']['mode'] not in gamemodes:
                            continue

                        win = True
                        if "result" in battle['battle'] and battle['battle']['result'] != "victory":
                            win = False
                        if "rank" in battle['battle'] and battle['battle']['mode'] == "soloShowdown" and battle['battle']['rank'] > 4:
                            win = False
                        if "rank" in battle['battle'] and battle['battle']['mode'] != "soloShowdown" and battle['battle']['rank'] > 2:
                            win = False

                        if type == "wins" and not win:
                            return

                        player = None
                        if "teams" in battle['battle']:
                            for t in battle['battle']['teams']:
                                for p in t:
                                    if p['tag'].replace("#", "") == tag.upper():
                                        player = p
                        else:
                            for p in battle['battle']['players']:
                                if p['tag'].replace("#", "") == tag.upper():
                                    player = p
                        if player is None:
                            await self.log_error(e)
                            continue

                        if "trophies" not in player['brawler']:
                            continue
                        if player['brawler']['trophies'] < min_trophy:
                            continue

                        brawler_name = player['brawler']['name']
                        if len(brawlers) > 1 and brawler_name not in brawlers:
                            return

                        score += 1
                    old = participants[str(mem_id)]["progress"]
                    await self.config.guild(labs).set_raw("active_challenges", chall_id, "participants", str(mem_id), value={"progress": old + score, "last": log[0]['battleTime']})
                    if score != 0:
                        await self.log(log_channel, f"[{chall_id}] {user.display_name} +{score}")

    @progress_update_loop.error
    async def progress_update_loop_errors(self, error):
        await self.log_error(error)

    async def log_error(self, error):
        traceback.print_exc()
        labs = self.bot.get_guild(self.labs)
        labs_log_id = await self.config.guild(labs).log()
        log_channel = labs.get_channel(labs_log_id)
        
        str_error = traceback.format_exception(type(error), error, error.__traceback__)
        wrapper = textwrap.TextWrapper(width=1000, max_lines=5, expand_tabs=False, replace_whitespace=False)
        messages = wrapper.wrap("".join(str_error))
        embed = discord.Embed(colour=discord.Color.red())
        
        for i, m in enumerate(messages[:5], start=1):
            embed.add_field(
                name=f"Part {i}",
                value="```py\n" + m + "```",
                inline=False
            )
        await log_channel.send(embed=embed)

    
    async def log(self, channel, message, colour=discord.Colour.green()):
        embed=discord.Embed(colour=colour, description=message)
        await channel.send(embed=embed)

    async def challenge_update(self):
        return

    async def challenge_finish(self):
        return

    def make_chall_embed(self, data, chal_id):
        starts = self.time_left((dt.strptime(data["start"], "%d/%m/%y %H:%M") - dt.now()).total_seconds())
        #ends = self.time_left((dt.strptime(data["end"], "%d/%m/%y %H:%M") - dt.now()).total_seconds())
        embed = discord.Embed(
            title = data["name"],
            description=data["description"] + f"\n\nJoin with `/ch join {chal_id}`",
            colour=discord.Colour.random()
        )
        embed.add_field(name="Starts in", value=starts, inline=False)
        if "rewards" in data:
            rewards = ""
            for threshold in data["rewards"]:
                rewards += f"[{threshold}]"
                if "normal" in data["rewards"][threshold]:
                    rewards += f" +{data['rewards'][threshold]['normal']}{self.token}"
                if "booster" in data["rewards"][threshold]:
                    rewards += f" <:booster:830158821132992543>+{data['rewards'][threshold]['booster']}{self.token}"
                rewards += "\n"
            if rewards != "":
                embed.add_field(name="Rewards", value=rewards, inline=False)
        if "global" in data:
            glob_rew = f"[{data['global']['goal']}] +{data['global']['reward']}{self.token}"
            embed.add_field(name="Server Goal", value=glob_rew, inline=False)
        if "image" in data:
            embed.set_thumbnail(url=data["image"])
        return embed
        


    @commands.guild_only()
    @commands.group(invoke_without_command=False, aliases=['chal', 'chall', 'ch'])
    async def challenge(self, ctx):
        return

    
    @checks.is_owner()
    @commands.guild_only()
    @challenge.command(name="channel")
    async def challenge_channel(self, ctx, channel:discord.TextChannel):
        await self.config.guild(ctx.guild).channel.set(channel.id)
        return await ctx.send("channel set to " + channel.mention)

    @checks.is_owner()
    @commands.guild_only()
    @challenge.command(name="log")
    async def challenge_log(self, ctx, channel:discord.TextChannel):
        await self.config.guild(ctx.guild).log.set(channel.id)
        return await ctx.send("log set to " + channel.mention)

    @commands.guild_only()
    @challenge.command(name="join")
    async def challenge_join(self, ctx, challenge_id:str):
        if ctx.guild.id != self.labs:
            return
        challs = await self.config.guild(ctx.guild).active_challenges()
        if challenge_id not in challs.keys():
            return await ctx.send(f"No challenge with ID {challenge_id} found!")
        bs_conf = self.get_bs_config()
        if (await bs_conf.user(ctx.author).tag()) is None:
            return await ctx.send("Save your tag using `/save` first!")
        if str(ctx.author.id) in challs[challenge_id]["participants"]:
            return await ctx.send(f"You are already participating in {challs[challenge_id]['name']}.")
        time = (dt.strptime(challs[challenge_id]["start"], "%d/%m/%y %H:%M")).strftime("%Y%m%dT%H%M%S.%fZ")
        await self.config.guild(ctx.guild).set_raw("active_challenges", challenge_id, "participants", str(ctx.author.id), value={"progress": 0, "last": time})
        return await ctx.send(f"{ctx.author.mention} sucessfully joined {challs[challenge_id]['name']}!")

    @commands.guild_only()
    @challenge.command(name="stats")
    async def challenge_stats(self, ctx, target: discord.Member = None):
        if ctx.guild.id != self.labs:
            return
        if target is None:
            target = ctx.author
        embed = discord.Embed(colour=discord.Colour.green())
        embed.set_author(name=f"{target.display_name}'s challenge stats", icon_url=target.avatar_url)
        embed.add_field(name="Tokens", value=await self.config.member(target).tokens(), inline=False)
        progress = ""
        challs = await self.config.guild(ctx.guild).active_challenges()
        for chall_id in challs:
            if str(target.id) in challs[chall_id]["participants"]:
                if challs[chall_id]['status'] == "start_soon":
                    progress += f"**{challs[chall_id]['name']}** `hasn't started yet`\n"
                else:
                    progress += f"**{challs[chall_id]['name']}** `{challs[chall_id]['participants'][str(target.id)]['progress']}`\n"
            else:
                progress += f"**{challs[chall_id]['name']}** `not participating`\n"
        embed.description = progress
        await ctx.send(embed=embed)
        
