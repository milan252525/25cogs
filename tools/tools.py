import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.embed import randomize_colour
from discord.ext import tasks
from datetime import datetime
from time import time
from random import choice
import random
from typing import Union
import asyncio
import upsidedown
from bs.utils import badEmbed
import aiohttp
#from profanity_check import predict, predict_prob
#from profanityfilter import ProfanityFilter


class Tools(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=2555525)
        default_global = {"countdowns": {}}
        default_member = {"messages": 0, "name": None}
        default_channel = {"sticky": False, "message": None, "last_id": None}
        self.config.register_global(**default_global)
        self.config.register_member(**default_member)
        self.config.register_channel(**default_channel)
        self.leave_counter = {}
        #self.pf = ProfanityFilter()
        self.updater.start()
        self.sticky_messages.start()
        # allow mentions on start
        self.bot.allowed_mentions = discord.AllowedMentions(roles=True)

    def cog_unload(self):
        self.updater.stop()
        self.sticky_messages.cancel()

    @commands.command()
    async def fliptext(self, ctx, *, text: str):
        await ctx.send(text[::-1])

    @commands.command()
    async def updown(self, ctx, *, text: str):
        await ctx.send(upsidedown.transform(text))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id not in self.leave_counter:
            self.leave_counter[member.guild.id] = [int(time())]
        else:
            self.leave_counter[member.guild.id].append(int(time()))
        if len(self.leave_counter[member.guild.id]) > 4:
            if self.leave_counter[member.guild.id][-1] - self.leave_counter[member.guild.id][-4] < 300:
                await self.bot.get_user(230947675837562880).send(f"Members in **{member.guild.name}** are disappearing too fast!")

    @commands.Cog.listener()
    async def on_message(self, msg):
        # CMG CUP staff ping ping
        if msg.guild.id == 1030444739289436250 and not msg.author.bot:
            staff_role = msg.guild.get_role(1030450401297846353)
            if staff_role in msg.role_mentions:
                ch = msg.channel
                category = msg.guild.get_channel(1048692861744451614)
                return await ch.edit(name=f"🔴│{ch.name}", category=category, topic=f"{ch.topic} [[{ch.category_id}]]")

    @commands.guild_only()
    @commands.has_role("Chasmac Cup Staff")
    @commands.command()
    async def solved(self, ctx):
        if ctx.guild.id != 1030444739289436250:
            return
        ch = ctx.channel
        if not ch.name.startswith("🔴"):
            return await ctx.send("This channel is not in Mediator category.")
        original_cat = ch.topic[ch.topic.find("[[")+2:ch.topic.find("]]")]
        if not original_cat.isdigit():
            return await ctx.send("Can't move back to original category.")
        await ch.edit(
            name=ch.name.replace("🔴│", ""),
            category=ctx.guild.get_channel(original_cat),
            topic=ch.topic.replace(f"[[{original_cat}]]", "")
        )

    @commands.guild_only()
    @commands.is_owner()
    @commands.command()
    async def spamadd(self, ctx, amount: int, member: discord.Member):
        value = await self.config.member(member).messages()
        await self.config.member(member).messages.set(value+amount)
        await self.config.member(member).name.set(member.display_name)
        await ctx.send("Done!")

    def convertToLeft(self, sec):
        if sec > 3600:
            return f"{int(sec/3600)} hours {int((sec%3600)/60)} minutes"
        elif sec > 60:
            return f"{int(sec/60)} minutes {int(sec%60)} seconds"
        else:
            return f"{sec} seconds"

    @tasks.loop(seconds=60.0)
    async def updater(self):
        countdowns = await self.config.countdowns()
        for m in countdowns.keys():
            chan = self.bot.get_channel(countdowns[m]["channel"])
            msg = await chan.fetch_message(m)
            now = int(time())
            finish = countdowns[m]["finish"]
            if now > finish:
                await self.config.countdowns.clear_raw(m)
                await msg.edit(embed=discord.Embed(description="Countdown ended!", colour=discord.Colour.red()))
            else:
                await msg.edit(embed=discord.Embed(description=f"Time left: {self.convertToLeft(finish-now)}", colour=discord.Colour.blue()))

    @updater.before_loop
    async def before_updater(self):
        await asyncio.sleep(10)

    @commands.command()
    async def countdown(self, ctx, amount: int, timeunit: str):
        """
        Start a countdown
        /countdown 1 h
        Accepted time units - s, m, h
        """

        if timeunit not in ["s", "m", "h", "seconds", "minutes", "hours", ]:
            return await ctx.send("Invalid time unit! Use \"s\", \"m\" or \"h\".")

        seconds = 0

        if timeunit == "s":
            seconds = amount
        elif timeunit == "m":
            seconds = amount * 60
        elif timeunit == "h":
            seconds = amount * 3600

        countdownMessage = await ctx.send(embed=discord.Embed(description=f"Time left: {self.convertToLeft(seconds)}", colour=discord.Colour.blue()))

        await self.config.countdowns.set_raw(countdownMessage.id, value={"finish": int(time()) + seconds, "channel": ctx.channel.id})
        await ctx.message.delete(delay=10)

    @commands.command()
    async def members(self, ctx, *, rolename):
        mentions = False
        if "mentions" in rolename:
            mentions = True
            rolename = rolename.replace("mentions", "").strip()
        role = None
        for r in ctx.guild.roles:
            if r.name.lower() == rolename.lower():
                role = r
                continue
            elif r.name.lower().startswith(rolename.lower()):
                role = r
                continue
        if role is None:
            await ctx.send("No such role in the server.")
            return
        result = role.members
        if not result:
            await ctx.send("No members with such role in the server.")
            return
        msg = f"Members: {str(len(result))}\n"
        messages = []
        for member in result:
            if len(msg) > 1999:
                messages.append(msg)
                msg = ""
            if mentions:
                msg += f"{member.mention}\n"
            else:
                msg += f"{str(member)}\n"
        if len(msg) > 0:
            messages.append(msg)
        for m in messages:
            if not mentions:
                m = m.replace('_', '\\_')
                m = m.replace('*', '\\*')
                m = m.replace('~', '\\~')
            await ctx.send(embed=discord.Embed(title=role.name, description=m, colour=discord.Colour.green()))

    @commands.command()
    async def members2(self, ctx, *rolenames):
        if len(rolenames) != 2:
            await ctx.send("Please enter two roles.")
            return
        roles = []
        for rolename in rolenames:
            for r in ctx.guild.roles:
                if r.name.lower() == rolename.lower():
                    roles.append(r)
                    continue
                elif r.name.lower().startswith(rolename.lower()):
                    roles.append(r)
                    continue
        if len(roles) < len(rolenames):
            await ctx.send("Not all roles were found.")
            return
        results = []
        for role in roles:
            results.append(role.members)
        result = list(set(results[0]) & set(results[1]))
        if len(result) == 0:
            await ctx.send("No members with such combination of roles in the server.")
            return
        msg = f"Members: {str(len(result))}\n"
        messages = []
        for member in result:
            if len(msg) > 1999:
                messages.append(msg)
                msg = ""
            msg += f"{str(member)}\n"
        if len(msg) > 0:
            messages.append(msg)
        for m in messages:
            m = m.replace('_', '\\_')
            m = m.replace('*', '\\*')
            m = m.replace('~', '\\~')
            await ctx.send(embed=discord.Embed(title=role.name, description=m, colour=discord.Colour.green()))

    # @commands.command()
    async def membersadvanced(self, ctx, *, settings):
        settings = settings.split(" ")
        if len(settings) % 2 != 0:
            return await ctx.send(embed=badEmbed("Looks like you entered the settings incorrectly."))
        people = []
        for i in range(len(settings)):
            if i % 2 != 0:
                continue
            role = None
            for r in ctx.guild.roles:
                if r.name.lower().startswith(settings[i + 1]):
                    role = r
            if role is None:
                return await ctx.send(embed=badEmbed(f"{settings[i + 1]} doesn't look like a valid role."))
            if settings[i] == "-r":
                for m in ctx.guild.members:
                    if role in m.roles:
                        if m in people:
                            people.remove(m)
            elif settings[i] == "-a":
                for m in ctx.guild.members:
                    if role in m.roles:
                        people.append(m)
        msg = ""
        for p in people:
            msg = msg + f"{str(p)}\n"
        await ctx.send(embed=discord.Embed(colour=discord.Colour.orange(), description=msg, title="Members:"))

    # @commands.command()
    async def membersall(self, ctx):
        user_ids = set()
        user_ids_online = set()
        servers = ""
        LA_guilds = sorted([guild for guild in self.bot.guilds if "LA" in guild.name],
                           key=lambda x: x.member_count, reverse=True)
        for guild in LA_guilds:
            if "LA" in guild.name:
                servers += f"[{guild.member_count}] {guild.name}\n"
                for mem in guild.members:
                    user_ids.add(mem.id)
                    if mem.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd):
                        user_ids_online.add(mem.id)
        await ctx.send(f"**Total unique accounts:** {len(user_ids)}\n**Currently online:** {len(user_ids_online)}\n**Servers**: ({len(LA_guilds)})\n```{servers[:1950]}```")

    # @commands.guild_only()
    # @commands.command()
    async def laban(self, ctx, member: Union[discord.Member, str], reason: str = ""):
        if ctx.author.id not in [614138334717149205, 230947675837562880]:
            return await ctx.send("You can't use this command.")
        # main labs lafc labsevents spain, academy, asia, bd, derucula, support, portugal, me
        guilds = [440960893916807188, 401883208511389716, 593248015729295360, 654334199494606848, 460550486257565697, 473169548301041674,
                  663716223258984496, 593732431551660063, 631888808224489482, 594736382727946250, 616673259538350084, 773750926578155541]
        msg = f"Attempting to ban **{member}** in all LA servers:"
        for id in guilds:
            try:
                guild = self.bot.get_guild(id)
                m = discord.Object(member.id if isinstance(
                    member, discord.Member) else member)
                await guild.ban(m, reason=f"Banned from all LA servers. Reason: {reason if reason != '' else 'not specified'}")
                msg += f"\n<:good:450013422717763609> **{guild.name}**"
            except discord.Forbidden:
                msg += f"\n<:bad:450013438756782081> **{guild.name}** (Forbidden to ban)"
            except discord.HTTPException as he:
                msg += f"\n<:bad:450013438756782081> **{guild.name}** ({he})"
            except AttributeError as he:
                msg += f"\n<:bad:450013438756782081> **{id}** ({he})"
            except Exception as e:
                msg += f"\n<:bad:450013438756782081> **{guild.name}** ({e})"
        await ctx.send(embed=discord.Embed(description=msg, colour=discord.Colour.red()))

    # @commands.guild_only()
    # @commands.command()
    async def launban(self, ctx, member: Union[discord.Member, str], reason: str = ""):
        if ctx.author.id not in [614138334717149205, 230947675837562880]:
            return await ctx.send("You can't use this command.")
        guilds = [440960893916807188, 401883208511389716, 593248015729295360, 654334199494606848, 460550486257565697, 473169548301041674,
                  663716223258984496, 593732431551660063, 631888808224489482, 594736382727946250, 616673259538350084, 773750926578155541]
        msg = f"Attempting to unban **{member}** in all LA servers:"
        for id in guilds:
            try:
                guild = self.bot.get_guild(id)
                m = discord.Object(member.id if isinstance(
                    member, discord.Member) else member)
                await guild.unban(m, reason=f"Banned from all LA servers. Reason: {reason if reason != '' else 'not specified'}")
                msg += f"\n<:good:450013422717763609> **{guild.name}**"
            except discord.Forbidden:
                msg += f"\n<:bad:450013438756782081> **{guild.name}** (Forbidden to unban)"
            except discord.HTTPException as he:
                msg += f"\n<:bad:450013438756782081> **{guild.name}** ({he})"
            except AttributeError as he:
                msg += f"\n<:bad:450013438756782081> **{id}** ({he})"
            except Exception as e:
                msg += f"\n<:bad:450013438756782081> **{guild.name}** ({e})"
        await ctx.send(embed=discord.Embed(description=msg, colour=discord.Colour.green()))

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command()
    async def stick(self, ctx, message_id: int):
        channel = ctx.channel
        try:
            message = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.HTTPException, discord.Forbidden):
            return await ctx.send("No message with provided ID found in this channel.")

        await self.config.channel(channel).sticky.set(True)
        await self.config.channel(channel).message.set(discord.utils.escape_mentions(message.content))
        embed = discord.Embed(colour=discord.Colour.blue(
        ), description=discord.utils.escape_mentions(message.content))
        sticky = await ctx.send(embed=embed)
        await self.config.channel(channel).last_id.set(sticky.id)

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command()
    async def unstick(self, ctx):
        channel = ctx.channel

        if not (await self.config.channel(channel).sticky()):
            return await ctx.send("No message to remove in this channel.")

        id = await self.config.channel(channel).last_id()
        try:
            message = await channel.fetch_message(id)
            await message.delete()
        except (discord.NotFound, discord.HTTPException, discord.Forbidden):
            pass

        await self.config.channel(channel).clear()
        m = await ctx.send("Sticky message removed successfully.")
        await m.delete(delay=5)

    @tasks.loop(seconds=15)
    async def sticky_messages(self):
        all = await self.config.all_channels()
        for channel_id in all:
            if not all[channel_id]["sticky"]:
                continue
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                continue
            if channel.last_message_id != all[channel_id]["last_id"]:
                old = await channel.fetch_message(all[channel_id]["last_id"])
                await old.delete()
                embed = discord.Embed(colour=discord.Colour.blue(
                ), description=all[channel_id]["message"])
                m = await channel.send(embed=embed)
                await self.config.channel(channel).last_id.set(m.id)

    @sticky_messages.before_loop
    async def before_sticky_messages(self):
        await asyncio.sleep(3)
