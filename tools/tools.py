import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.embed import randomize_colour
from discord.ext import tasks
from datetime import datetime
from time import time
from random import choice

class Tools(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=2555525)
        default_global = {"countdowns" : {}}
        default_member = {"messages" : 0, "name" : None}
        self.config.register_global(**default_global)
        self.config.register_member(**default_member)    
        self.updater.start()
        
    def cog_unload(self):
        self.updater.stop()
        
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
                    await msg.channel.send(f"Wrong number! (Hint: {numberPrev} + 1)", delete_after=2)
                    return await msg.delete()
                if msg.author == history[1].author:
                    await msg.channel.send(f"Slow down! Let other people count as well!", delete_after=2)
                    return await msg.delete()
            except ValueError:
                await msg.delete()

        #LABS giveaway
        if not msg.author.bot and isinstance(msg.channel, discord.TextChannel) and msg.guild.id == 401883208511389716 and (msg.channel.category_id == 401883208511389717 or msg.channel.category_id == 576000643135963136):
            amount = await self.config.member(msg.author).messages()
            await self.config.member(msg.author).messages.set(amount + 1)
            await self.config.member(msg.author).name.set(msg.author.display_name)
                
        #message redirection
        if not msg.author.bot and isinstance(msg.channel, discord.abc.PrivateChannel) and not (msg.author.id == 230947675837562880):
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

    @commands.guild_only()
    @commands.is_owner() 
    @commands.command()
    async def spamlb(self, ctx):
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
        await self.bot.wait_until_ready()
        
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
    async def postjob(self, ctx):
        author = ctx.author
        intro = await ctx.send("Please head over to a DM with me to answer some questions.")
        await ctx.message.delete(delay=10)
        await intro.delete(delay=10)
        jobChannel = self.bot.get_channel(602906639217197085)
        
        def check(msg):
            return msg.channel == author.dm_channel and msg.author == author
        
        await author.send("Is this job posting or position opening:")
        job = (await self.bot.wait_for('message', check=check)).content
        await author.send("Completion deadline:")
        deadline = (await self.bot.wait_for('message', check=check)).content
        await author.send("Availability (who can apply for this job?):")
        availability = (await self.bot.wait_for('message', check=check)).content
        await author.send("How should interested people contact you:")
        contact = (await self.bot.wait_for('message', check=check)).content
        await author.send("Description of the job:")
        jobdesc = (await self.bot.wait_for('message', check=check)).content
        await author.send(f"Done! Your offer was posted in {jobChannel.mention}")
        
        embed=discord.Embed(title=job)
        embed.set_thumbnail(url=author.avatar_url)
        embed.add_field(name="Posted by:", value=f"{author.mention} ({author.top_role})", inline=False)
        embed.add_field(name="Date:", value=datetime.now().strftime('%d %b %Y'), inline=False)
        embed.add_field(name="Completion deadline:", value=deadline, inline=False)
        embed.add_field(name="Availability:", value=availability, inline=False)
        embed.add_field(name="How to contact:", value=contact, inline=False)
        embed.add_field(name="Job description:", value=jobdesc, inline=False)
        
        
        await jobChannel.send(embed=randomize_colour(embed))

    @commands.command()
    async def members(self, ctx, *, rolename):
        role = discord.utils.get(ctx.guild.roles, name=rolename)
        if role is None:
            await ctx.send("No such role in the server.")
            return
        result = role.members
        if not result:
            await ctx.send("No members with such role in the server.")
            return
        msg = ""
        messages = []
        for member in result:
            if len(msg) > 1999:
                messages.append(msg)
                msg = ""
            msg += f"{member.mention}\n"
        if len(msg) > 0:
            messages.append(msg)
        for m in messages:
            await ctx.send(embed=discord.Embed(description=m, colour=discord.Colour.green()))
