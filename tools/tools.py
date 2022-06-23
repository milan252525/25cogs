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
        default_global = {"countdowns" : {}}
        default_member = {"messages" : 0, "name" : None}
        default_channel = {"sticky" : False, "message" : None, "last_id" : None}
        self.config.register_global(**default_global)
        self.config.register_member(**default_member)
        self.config.register_channel(**default_channel)
        self.leave_counter = {}
        #self.pf = ProfanityFilter()
        self.updater.start()
        self.sticky_messages.start()
        #allow mentions on start
        self.bot.allowed_mentions = discord.AllowedMentions(roles=True)
        
    def cog_unload(self):
        self.updater.stop()
        self.sticky_messages.cancel()
        
    @commands.command()
    async def fliptext(self, ctx, *, text:str):
        await ctx.send(text[::-1])

    @commands.command()
    async def updown(self, ctx, *, text:str):
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
        #counting DISABLED
        if False and msg.channel.id == 584099500612780053 and not msg.author.bot:
            try:
                number = int(msg.content.split(" ")[0])
                history = await msg.channel.history(limit=2).flatten()
                try:
                    numberPrev = int(history[1].content.split(" ")[0])
                except:
                    numberPrev = int(history[2].content.split(" ")[0])
                if number != numberPrev + 1:
                    return await msg.delete()
                if msg.author == history[1].author:
                    return await msg.delete()
            except ValueError:
                await msg.delete()

        #word-chain DISABLED
        if False and msg.channel.id == 670726361085902878 and not msg.author.bot:
            try:
                word = msg.content
                history = await msg.channel.history(limit=2).flatten()
                if word[0].lower() != history[1].content[-1].lower():
                    await msg.channel.send(f"Write a word that starts with **{history[1].content[-1:].capitalize()}**, please.", delete_after=2)
                    return await msg.delete()
                if msg.author == history[1].author:
                    await msg.channel.send(f"Don't write two words consecutively.", delete_after=2)
                    return await msg.delete()
                if len(word) < 3:
                    await msg.channel.send(f"Use words with atleast 3 letters.", delete_after=2)
                    return await msg.delete()
                if len(word.split(" ")) > 3:
                    await msg.channel.send(f"Use at most 3 words.", delete_after=2)
                    return await msg.delete()
            except ValueError:
                await msg.delete()
                
        #message redirection
        if not msg.author.bot and isinstance(msg.channel, discord.abc.PrivateChannel) and not (msg.author.id == 230947675837562880):
            if (self.bot.get_cog("Events").bf_active):
                return
            embed = discord.Embed(description = "Someone DMed me!", colour = discord.Colour.teal())
            embed.add_field(name="From: ", value=msg.author.name, inline=False)
            embed.add_field(name="ID: ", value=msg.author.id, inline=False)
            if msg.content == "":
                ctn = "Empty message :shrug:"
            else:
                ctn = msg.content
            embed.add_field(name="Message:", value=ctn, inline=False)
            if msg.attachments:
                for i in range(len(msg.attachments)):
                    embed.add_field(name=f"Attachment {str(i+1)}:", value=msg.attachments[i].url, inline=False)
            await self.bot.get_user(230947675837562880).send(embed=embed)
            
        #profanity filter
        #disabled
        if False and msg.guild.id == 401883208511389716 and not msg.author.bot:
            message_profanity = predict([msg.content])
            if message_profanity[0] == 1 or self.pf.is_profane(msg.content):
                info = f"[**{msg.author.display_name}**] {msg.channel.mention}: *{msg.content}*"
                return await msg.guild.get_channel(664514537004859436).send(info)
            message_profanity_prob = predict_prob([msg.content.replace("/", "")])
            if message_profanity_prob[0] > 0.35:
                info = f"[**{msg.author.display_name}**] ({message_profanity_prob[0]*100}%) {msg.channel.mention}: *{msg.content}*"
                await msg.guild.get_channel(664514537004859436).send(info)

        #spamlb LA Asia DISABLED
        if False and not msg.author.bot and isinstance(msg.channel, discord.TextChannel) and msg.channel.id in (663804057848250368, 663804237485965312):
            amount = await self.config.member(msg.author).messages()
            await self.config.member(msg.author).messages.set(amount + 1)
            await self.config.member(msg.author).name.set(msg.author.display_name)

    @commands.guild_only()
    @commands.is_owner()
    @commands.command()
    async def spamadd(self, ctx, amount: int, member: discord.Member):
        value = await self.config.member(member).messages()
        await self.config.member(member).messages.set(value+amount)
        await self.config.member(member).name.set(member.display_name)
        await ctx.send("Done!")
            
    #spamlb LA Asia
    #@commands.guild_only()
    #@commands.command()
    async def spamlb(self, ctx):
        if ctx.channel.id != 666655288606195735:
            return await ctx.send("You can't use that here")
        data = await self.config.all_members(ctx.guild)
        members = []
        for k in data.keys():
            members.append([data[k]["name"], data[k]["messages"]])
        members.sort(key=lambda x: x[1], reverse=True)
        msg = ""
        messages = []
        for p in members:
            if len(msg) > 1500:
                messages.append(msg)
                msg = ""
            msg += f"{p[0]} `{p[1]}`\n"
        if len(msg) > 0:
            messages.append(msg)
        for m in messages:
            await ctx.send(embed=discord.Embed(description=m, colour=discord.Colour.gold()))

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
    async def countdown(self, ctx, amount : int, timeunit : str):
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

        await self.config.countdowns.set_raw(countdownMessage.id, value={"finish" : int(time()) + seconds, "channel" : ctx.channel.id})
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

    @commands.command()
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

    @commands.command()
    async def membersall(self, ctx):
        user_ids = set()
        user_ids_online = set()
        servers = ""
        LA_guilds = sorted([guild for guild in self.bot.guilds if "LA" in guild.name], key=lambda x: x.member_count, reverse=True)
        for guild in LA_guilds:
            if "LA" in guild.name:
                servers += f"[{guild.member_count}] {guild.name}\n"
                for mem in guild.members:
                    user_ids.add(mem.id)
                    if mem.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd):
                        user_ids_online.add(mem.id)
        await ctx.send(f"**Total unique accounts:** {len(user_ids)}\n**Currently online:** {len(user_ids_online)}\n**Servers**: ({len(LA_guilds)})\n```{servers[:1950]}```")

    @commands.guild_only()
    @commands.command()
    async def laban(self, ctx, member:Union[discord.Member, str], reason:str=""):
        if ctx.author.id not in [614138334717149205, 230947675837562880]:
            return await ctx.send("You can't use this command.")
        #main labs lafc labsevents spain, academy, asia, bd, derucula, support, portugal, me
        guilds = [440960893916807188, 401883208511389716, 593248015729295360, 654334199494606848, 460550486257565697, 473169548301041674, 663716223258984496, 593732431551660063, 631888808224489482, 594736382727946250, 616673259538350084, 773750926578155541]
        msg = f"Attempting to ban **{member}** in all LA servers:"
        for id in guilds:
            try:
                guild = self.bot.get_guild(id)
                m = discord.Object(member.id if isinstance(member, discord.Member) else member)
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

    @commands.guild_only()
    @commands.command()
    async def launban(self, ctx, member: Union[discord.Member, str], reason:str=""):
        if ctx.author.id not in [614138334717149205, 230947675837562880]:
            return await ctx.send("You can't use this command.")
        guilds = [440960893916807188, 401883208511389716, 593248015729295360, 654334199494606848, 460550486257565697, 473169548301041674, 663716223258984496, 593732431551660063, 631888808224489482, 594736382727946250, 616673259538350084, 773750926578155541]
        msg = f"Attempting to unban **{member}** in all LA servers:"
        for id in guilds:
            try:
                guild = self.bot.get_guild(id)
                m = discord.Object(member.id if isinstance(member, discord.Member) else member)
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
        embed = discord.Embed(colour=discord.Colour.blue(), description=discord.utils.escape_mentions(message.content))
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
                embed = discord.Embed(colour=discord.Colour.blue(), description=all[channel_id]["message"])
                m = await channel.send(embed=embed)
                await self.config.channel(channel).last_id.set(m.id)
        
    @sticky_messages.before_loop
    async def before_sticky_messages(self):
        await asyncio.sleep(3)
