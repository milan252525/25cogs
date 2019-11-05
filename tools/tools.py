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
        self.config.register_global(**default_global)
        self.updater.start()
        
    def cog_unload(self):
        self.updater.stop()
        
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.channel.id == 584099500612780053 and not msg.author.bot:
            try:
                number = int(msg.content.split(" ")[0])
                history = await msg.channel.history(limit=2).flatten()
                try:
                    numberPrev = int(history[1].content.split(" ")[0])
                except:
                    numberPrev = int(history[2].content.split(" ")[0])
                if number != numberPrev + 1:
                    wrongmsg = ["Wrong number!", "I know math is hard... Try using a calculator maybe?", "Improve your counting skils...", "Did you not go to school?", "Thats wrong...", "https://en.wikipedia.org/wiki/Counting", "Try again...", "Mirror, mirror on the wall, who’s the smartest of them all? NOT YOU!"]
                    await msg.channel.send(f"{choice(wrongmsg)} (Hint: {numberPrev} + 1)", delete_after=2)
                    return await msg.delete()
                if msg.author == history[1].author:
                    await msg.channel.send(f"Slow down! Let other people count as well!", delete_after=2)
                    return await msg.delete()
            except ValueError:
                await msg.delete()
                

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
        
        
        
        
        

