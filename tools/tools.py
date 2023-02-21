import asyncio
from time import time
from typing import Union

import discord
import upsidedown
from bs.utils import badEmbed
from discord.ext import tasks
from redbot.core import Config, commands


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

    # @commands.command()
    # async def submit(self, ctx, *, text: str = ""):
    #     if text == "" and not ctx.message.attachments:
    #         msg = await ctx.send(embed=discord.Embed(title=f"Do not submit empty message with no attachments. {ctx.prefix}submit <content>", colour=discord.Colour.red()))
    #         await msg.delete(delay=10)
    #     target = self.bot.get_channel(722486276288282744)  # admin-bot-tests

    #     if ctx.message.attachments:
    #         files = []
    #         for attach in ctx.message.attachments:
    #             try:
    #                 files.append(await attach.to_file())
    #             except:
    #                 continue
    #         await target.send(content=f"__{ctx.author.mention} [{ctx.author.id}] submitted:__\n{text[:1950]}", files=files[:10])
    #     else:
    #         await target.send(content=f"__{ctx.author.mention} [{ctx.author.id}] submitted:__\n{text[:1950]}")
    #     await ctx.message.delete()
    #     await ctx.send(f"{ctx.author.mention} your submission has been received.")

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
