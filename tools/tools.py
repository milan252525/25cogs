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
    async def on_command(self, ctx):
        if ctx.author.id == 230947675837562880:
            return
        link = (await self.bot.get_shared_api_tokens("webhook"))["link"]
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(link, adapter=discord.AsyncWebhookAdapter(session))
            await webhook.send(f"[{ctx.guild.name}]\n[{ctx.author.id}]\n{ctx.message.content}", username=f"{ctx.author.name}", avatar_url=ctx.author.avatar_url)
    
    @commands.Cog.listener()
    async def on_message(self, msg):
        #counting
        if msg.channel.id == 584099500612780053 and not msg.author.bot:
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

        #word-chain
        if msg.channel.id == 670726361085902878 and not msg.author.bot:
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


    @commands.guild_only()
    @commands.command()
    async def laban(self, ctx, member:Union[discord.Member, str]):
        if ctx.author.id not in [355514130737922048, 781512318760255488, 585275812429824041, 230947675837562880]:
            return await ctx.send("You can't use this command.")
        #main labs lafc labsevents spain, academy, asia, bd, derucula, support, portugal, me
        guilds = [440960893916807188, 401883208511389716, 593248015729295360, 654334199494606848, 460550486257565697, 473169548301041674, 663716223258984496, 593732431551660063, 631888808224489482, 594736382727946250, 616673259538350084, 773750926578155541]
        msg = f"Attempting to ban **{member}** in all LA servers:"
        for id in guilds:
            try:
                guild = self.bot.get_guild(id)
                m = discord.Object(member.id if isinstance(member, discord.Member) else member)
                await guild.ban(m, reason="Banned from all LA servers.")
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
    async def launban(self, ctx, member: Union[discord.Member, str]):
        if ctx.author.id not in [355514130737922048, 781512318760255488, 585275812429824041, 230947675837562880]:
            return await ctx.send("You can't use this command.")
        guilds = [440960893916807188, 401883208511389716, 593248015729295360, 654334199494606848, 460550486257565697, 473169548301041674, 663716223258984496, 593732431551660063, 631888808224489482, 594736382727946250, 616673259538350084, 773750926578155541]
        msg = f"Attempting to unban **{member}** in all LA servers:"
        for id in guilds:
            try:
                guild = self.bot.get_guild(id)
                m = discord.Object(member.id if isinstance(member, discord.Member) else member)
                await guild.unban(m, reason="Unbanned from all LA servers.")
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

    @commands.command()
    async def announcement(self, ctx, *, message):
        guilds = dict()
        guilds[663416919646535695] = 663418966475145277 #la announcement test
        guilds[401883208511389716] = 402131630497464340 #LA Gaming - Brawl Stars
        guilds[440960893916807188] = 538380432748838912 #LA Gaming
        guilds[460550486257565697] = 590976482319269928 #LA Spain
        guilds[593248015729295360] = 593310903055941634 #LA Fight Club
        guilds[609481228562857985] = 609484084095352842 #LA Gaming - Competitive
        guilds[609857211208040450] = 648967703142596608 #LA eSports
        guilds[655889917821321217] = 655909661257498635 #LA Poland BS
        guilds[663716223258984496] = 663803783318339584 #LA Asia
        guilds[594736382727946250] = 594736382732140545 #LA Leadership

        if ctx.author.id != 355514130737922048 and ctx.author.id != 781512318760255488 and ctx.author.id != 585275812429824041:
            await ctx.send("You can't use this command.")
            return

        everyone = False
        everyonemessage = await ctx.send("Do you want to mention everyone?")
        await everyonemessage.add_reaction("<:yesconfirm:595535992329601034>")
        await everyonemessage.add_reaction("<:nocancel:595535992199315466>")

        def check(reaction, user):
            return (user == ctx.author or user.id == 230947675837562880) and str(reaction.emoji) in [
                "<:yesconfirm:595535992329601034>", "<:nocancel:595535992199315466>"]

        reaction, _ = await self.bot.wait_for('reaction_add', check=check)

        if str(reaction.emoji) == "<:yesconfirm:595535992329601034>":
            everyone = True

        mentions = []
        mentionsmessage = await ctx.send("Do you want to mention other roles?")
        await mentionsmessage.add_reaction("<:yesconfirm:595535992329601034>")
        await mentionsmessage.add_reaction("<:nocancel:595535992199315466>")

        def check(reaction, user):
            return (user == ctx.author or user.id == 230947675837562880) and str(reaction.emoji) in [
                "<:yesconfirm:595535992329601034>", "<:nocancel:595535992199315466>"]

        reaction, _ = await self.bot.wait_for('reaction_add', check=check)

        if str(reaction.emoji) == "<:yesconfirm:595535992329601034>":
            await ctx.send("List IDs of the roles you want to mention, separated by a space.")

            def checkmsg(m):
                return m.channel == ctx.channel and m.author == ctx.author

            msg = await self.bot.wait_for('message', check=checkmsg)
            mentions = msg.content.split(' ')

        links = dict()
        linksmessage = await ctx.send("Do you want to send links?")
        await linksmessage.add_reaction("<:yesconfirm:595535992329601034>")
        await linksmessage.add_reaction("<:nocancel:595535992199315466>")

        def check(reaction, user):
            return (user == ctx.author or user.id == 230947675837562880) and str(reaction.emoji) in [
                "<:yesconfirm:595535992329601034>", "<:nocancel:595535992199315466>"]

        reaction, _ = await self.bot.wait_for('reaction_add', check=check)

        if str(reaction.emoji) == "<:yesconfirm:595535992329601034>":
            await ctx.send("List the link names and links, separated by \" + \", e.g. \"twitter + twitter.com + instagram + instagram.com\". Warning: don't enter a link without a name!")

            def checkmsg(m):
                return m.channel == ctx.channel and m.author == ctx.author

            msg = await self.bot.wait_for('message', check=checkmsg)
            linkstemp = msg.content.split(' + ')
            for i in range(len(linkstemp) - 1):
                if i % 2 != 0:
                    continue
                links[linkstemp[i]] = linkstemp[i + 1]

        all = False
        allmessage = await ctx.send("Send an announcement to all available servers?")
        await allmessage.add_reaction("<:yesconfirm:595535992329601034>")
        await allmessage.add_reaction("<:nocancel:595535992199315466>")

        def check(reaction, user):
            return (user == ctx.author or user.id == 230947675837562880) and str(reaction.emoji) in [
                "<:yesconfirm:595535992329601034>", "<:nocancel:595535992199315466>"]

        reaction, _ = await self.bot.wait_for('reaction_add', check=check)

        if str(reaction.emoji) == "<:yesconfirm:595535992329601034>":
            all = True

        elif str(reaction.emoji) == "<:nocancel:595535992199315466>":
            await ctx.send("Choose the servers to send the announcement to.")

        for key in guilds:
            guild = self.bot.get_guild(key)
            if all:
                ch = self.bot.get_channel(guilds[key])
                embed = discord.Embed(colour=discord.Colour.green(), description=message)
                await ch.send(embed=embed)

                pings = "Attention to: "
                if everyone:
                    pings += str(ch.guild.default_role) + ", "
                for mention in mentions:
                    role = discord.utils.get(ch.guild.roles, id=int(mention))
                    if role is None:
                        continue
                    elif role in ch.guild.roles:
                        await ctx.send(f"Mentioned role **{str(role)}** in **{guild.name}**.")
                        pings += role.mention + ", "
                if pings != "Attention to: ":
                    await ch.send(pings[:-2])

                linksmsg = ""
                for key in links:
                    linksmsg += key + ": " + links[key] + "\n"
                if linksmsg != "":
                    await ch.send(linksmsg)

                for attach in ctx.message.attachments:
                    fileembed = discord.Embed(color=discord.Colour.green())
                    fileembed.set_image(url=attach.url)
                    await ch.send(embed=fileembed)
            elif not all:
                checkmessage = await ctx.send(f"Do you want to send an announcement to **{guild.name}**?")
                await checkmessage.add_reaction("<:yesconfirm:595535992329601034>")
                await checkmessage.add_reaction("<:nocancel:595535992199315466>")

                def check(reaction, user):
                    return (user == ctx.author or user.id == 230947675837562880) and str(reaction.emoji) in [
                        "<:yesconfirm:595535992329601034>", "<:nocancel:595535992199315466>"]

                reaction, _ = await self.bot.wait_for('reaction_add', check=check)

                if str(reaction.emoji) == "<:yesconfirm:595535992329601034>":
                    ch = self.bot.get_channel(guilds[key])
                    embed = discord.Embed(colour=discord.Colour.green(), description=message)
                    await ch.send(embed=embed)

                    pings = "Attention to: "
                    if everyone:
                        pings += str(ch.guild.default_role) + ", "
                    for mention in mentions:
                        role = discord.utils.get(ch.guild.roles, id=int(mention))
                        if role is None:
                            continue
                        elif role in ch.guild.roles:
                            await ctx.send(f"Mentioned role **{str(role)}** in **{guild.name}**.")
                            pings += role.mention + ", "
                    if pings != "Attention to: ":
                        await ch.send(pings[:-2])

                    linksmsg = ""
                    for key in links:
                        linksmsg += key + ": " + links[key] + "\n"
                    if linksmsg != "":
                        await ch.send(linksmsg)

                    for attach in ctx.message.attachments:
                        fileembed = discord.Embed(color=discord.Colour.green())
                        fileembed.set_image(url=attach.url)
                        await ch.send(embed=fileembed)

                    await checkmessage.remove_reaction("<:yesconfirm:595535992329601034>", self.bot.get_user(599286708911210557))
                    await checkmessage.remove_reaction("<:nocancel:595535992199315466>", self.bot.get_user(599286708911210557))
                    await checkmessage.edit(content=f"Announced in **{guild.name}**.")

                elif str(reaction.emoji) == "<:nocancel:595535992199315466>":
                    await checkmessage.remove_reaction("<:yesconfirm:595535992329601034>", self.bot.get_user(599286708911210557))
                    await checkmessage.remove_reaction("<:nocancel:595535992199315466>", self.bot.get_user(599286708911210557))
                    await checkmessage.edit(content=f"Skipped **{guild.name}**.")

    @commands.command()
    @commands.guild_only()
    async def request(self, ctx):
        if ctx.guild.id != 594736382727946250:
            await ctx.send("Can't be used in this server.")

        programming = self.bot.get_channel(672139829361770496)
        graphics = self.bot.get_channel(672161329263411242)
        author = ctx.author
        intro = await ctx.send("Please head over to a DM with me to answer some questions.")
        await ctx.message.delete(delay=10)
        await intro.delete(delay=10)

        def check(msg):
            return msg.channel == author.dm_channel and msg.author == author

        gfx = False
        gfxstaff = ctx.guild.get_role(663233286134431774)
        ch = None
        await author.send(
            "Is it a graphics or programming request? (graphics/programming) (or send \"cancel\" without quotes to cancel the request)")
        channel = (await self.bot.wait_for('message', check=check)).content
        if channel.lower() == "graphics":
            gfx = True
            ch = graphics
        elif channel.lower() == "programming":
            ch = programming
        elif channel.lower() == "cancel":
            await author.send("Request cancelled.")
            return
        else:
            await author.send("Wrong argument! Try using /request command again.")
            return
        await author.send("Description of the job: (or send \"cancel\" without quotes to cancel the request)")
        jobdesc = (await self.bot.wait_for('message', check=check)).content
        if jobdesc.lower() == "cancel":
            await author.send("Request cancelled.")
            return
        await author.send(
            "How should interested people contact you: (or send \"cancel\" without quotes to cancel the request)")
        contact = (await self.bot.wait_for('message', check=check)).content
        if contact.lower() == "cancel":
            await author.send("Request cancelled.")
            return
        await author.send("You're all set! Request sent.")

        embed = discord.Embed(title=f"{channel.capitalize()} request", colour=discord.Colour.red())
        embed.set_thumbnail(url=author.avatar_url)
        embed.add_field(name="Posted by:", value=f"{author.mention} ({author.top_role})", inline=False)
        embed.add_field(name="Date:", value=datetime.now().strftime('%d %b %Y'), inline=False)
        embed.add_field(name="Job description:", value=jobdesc, inline=False)
        embed.add_field(name="How to contact:", value=contact, inline=False)

        if gfx:
            await ch.send(
                f"{gfxstaff.mention} Please, don't forget to use /acceptrequest ID if you start working on the request.")
        elif not gfx:
            await ch.send("Please, don't forget to use /acceptrequest ID if you start working on the request.")
        request = await ch.send(embed=embed)

        embed.add_field(name="ID:", value=request.id, inline=False)
        await request.edit(embed=embed)


    @commands.command()
    async def acceptrequest(self, ctx, *, messageid):
        author = ctx.author
        intro = await ctx.send("Please head over to a DM with me to answer some questions.")
        await ctx.message.delete(delay=10)
        await intro.delete(delay=10)

        def check(msg):
            return msg.channel == author.dm_channel and msg.author == author

        await author.send("Add a comment. It can be the time you need to do the task, immediate questions that arise, etc.")
        comment = (await self.bot.wait_for('message', check=check)).content
        await author.send("You're all set! Request accepted.")

        programming = self.bot.get_channel(672139829361770496)
        graphics = self.bot.get_channel(672161329263411242)

        try:
            msg = await programming.fetch_message(messageid)
        except:
            msg = await graphics.fetch_message(messageid)

        author = ""
        date = ""
        desc = ""
        contact = ""
        for embed in msg.embeds:
            title = embed.title
            author = embed.fields[0].value
            date = embed.fields[1].value
            desc = embed.fields[2].value
            contact = embed.fields[3].value

        embed = discord.Embed(title=title, colour=discord.Colour.green())
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.add_field(name="Posted by:", value=author, inline=False)
        embed.add_field(name="Date:", value=date, inline=False)
        embed.add_field(name="Job description:", value=desc, inline=False)
        embed.add_field(name="How to contact:", value=contact, inline=False)
        embed.add_field(name="Accepted by:", value=f"{ctx.author.mention} ({ctx.author.top_role})", inline=False)
        embed.add_field(name="Comment by an executor:", value=comment, inline=False)
        await msg.edit(embed=embed)

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

    @tasks.loop(seconds=30)
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
