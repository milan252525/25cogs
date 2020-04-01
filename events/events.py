import discord
from redbot.core import commands, Config, checks
from redbot.core.data_manager import cog_data_path
from discord.ext import tasks
from asyncio import sleep, TimeoutError
from random import choice, randint
from copy import copy
from time import time
import yaml
import re


class Events(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=2567124825)
        self.config.register_global(
            boss_hp=5000
        )
        default_user = {"boss_fight": {"damage" : 0, "participated" : 0}}
        self.config.register_member(**default_user)
        self.DAMAGE_PER_CHALL = 200
        self.START_WAIT_TIME = 60
        self.DAMAGE_EMOJI = "<:damage:643539221428174849>"
        self.HP_EMOJI = "<:health:688109898508009611>"
        self.LOG_EMOJI = "<:log:688112584368586779>"
        self.WAITING_EMOJI = "<:dyna:688120749323845637>"
        self.bf_data = None
        self.bf_active = False
        with open(str(cog_data_path(self)).replace("Events", r"CogManager/cogs/events/geo.yaml")) as file:
            self.geo_questions = yaml.load(file, Loader=yaml.FullLoader)
        with open(str(cog_data_path(self)).replace("Events", r"CogManager/cogs/events/trivia.yaml")) as file:
            self.trivia_questions = yaml.load(file, Loader=yaml.FullLoader)
        with open(str(cog_data_path(self)).replace("Events", r"CogManager/cogs/events/longwords.txt")) as file:
            self.longwords = []
            line = file.readline()
            while line != "":
                self.longwords.append(line.replace("\n", ""))
                line = file.readline()

    async def main_loop(self):
        while self.bf_data['hp_left'] > 0:
            chall = choice(("word", "math", "geo", "trivia")) 
            #start random challenge
            if chall == "word":
                res = await self.word_chall()
            elif chall == "math":
                res = await self.math_chall()
            elif chall == "geo":
                res = await self.geo_chall()
            elif chall == "trivia":
                res = await self.trivia_chall()
            #process results
            damage = 0
            log = ""
            dealt = self.DAMAGE_PER_CHALL
            for m in res:
                damage += dealt
                log += f"{self.DAMAGE_EMOJI}{m.display_name} `{dealt}`\n"
                if m.id not in self.bf_data["players"]:
                    self.bf_data["players"][m.id] = dealt
                else:
                    self.bf_data["players"][m.id] += dealt
                dealt = (dealt - 5) if dealt > 100 else dealt
            log = "Noone was successful!" if log == "" else log
            self.bf_data['hp_left'] -= damage
            #update action log
            embed = self.bf_data["embed"]
            embed.set_field_at(0, name=f"{self.HP_EMOJI} HP Left", value=f"{self.bf_data['hp_left']}/{await self.config.boss_hp()}", inline=False)
            embed.set_field_at(1, name=f"{self.LOG_EMOJI} Action log:", value=log)
            await self.bf_data["message"].edit(embed=embed)
            if self.bf_data['hp_left'] > 0:
                await sleep(randint(10, 20))

        #finish
        embed = self.bf_data["embed"]
        embed.set_thumbnail(url="https://i.imgur.com/fo3Tqfd.png")
        embed.set_field_at(0, name=f"{self.HP_EMOJI} HP Left", value=f"0/{await self.config.boss_hp()}", inline=False)
        embed.set_field_at(1, name=f"{self.LOG_EMOJI} Action log:", value="Boss has been defeated!")
        embed.set_footer(text="Good job!")
        await self.bf_data["message"].edit(embed=embed)
        
        final = []
        for pid, pdmg in self.bf_data["players"].items():
            final.append([pid, pdmg])
        final.sort(key=lambda x: x[1], reverse=True)
        
        msg = ""
        messages = []
        for p in final:
            if len(msg) > 1800:
                messages.append(msg)
                msg = ""
            u = self.bf_data["channel"].guild.get_member(p[0])
            if u is not None:
                await self.config.member(u).boss_fight.damage.set(await self.config.member(u).boss_fight.damage()+p[1])
                await self.config.member(u).boss_fight.participated.set(await self.config.member(u).boss_fight.participated()+1)
                msg += f"{u.mention} <:damage:643539221428174849> `{p[1]}`\n"
        if len(msg) > 0:
            messages.append(msg)
        for m in messages:
            await self.bf_data["channel"].send(embed=discord.Embed(title="Damage leaderboard", description=m, colour=discord.Colour.gold()))
        self.bf_active = False
            
    async def math_chall(self):
        limit = 15
        start = time()
        op = choice(("+", "-", "*", "/"))
        if op == "+":
            num1, num2 = randint(10, 500), randint(10, 500)
            result = num1 + num2
        elif op == "-":
            num1, num2 = randint(20, 500), randint(20, 300)
            if num2 > num1:
                num1, num2 = num2, num1
            result = num1 - num2
        elif op == "*":
            num1, num2 = randint(1, 50), randint(2, 15)
            if num2 > num1:
                num1, num2 = num2, num1
            result = num1 * num2
        elif op == "/":
            num2 = randint(1, 30)
            num1 = randint(1, 50) * num2
            result = num1 // num2
                               
        embed = discord.Embed(title="MATH CHALLENGE", description=f"You have {limit} seconds to write a result of:\n\n`{num1} {op} {num2}`", colour=discord.Color.magenta())
        embed.set_footer(text="Do not use calculator!")
        message = await self.bf_data["channel"].send(embed=embed)
        def check(m):
            return not m.author.bot and str(result) in m.content.lower() and m.channel == self.bf_data["channel"]
        success = []
        while time() - start < limit:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=3)
                if msg.author not in success:
                    success.append(msg.author)
            except TimeoutError:
                pass
        await message.edit(embed=discord.Embed(title="MATH CHALLENGE", description=f"The right answer was `{result}`", colour=discord.Color.dark_magenta()))
        await message.delete(delay=5)
        return success
        
    async def word_chall(self):
        word = choice(self.longwords)
        limit = 10
        start = time()
        embed = discord.Embed(title="TYPING CHALLENGE", description=f"You have {limit} seconds to type:\n\n`{word.upper()}`", colour=discord.Color.blue())
        embed.set_footer(text="Letter case doesn't matter. NO COPY PASTING!")
        message = await self.bf_data["channel"].send(embed=embed)
        def check(m):
            return not m.author.bot and word in m.content.lower() and m.channel == self.bf_data["channel"]
        success = []
        while time() - start < limit:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=3)
                if msg.author not in success:
                    success.append(msg.author)
            except TimeoutError:
                pass
        await message.delete() 
        return success
 
    async def geo_chall(self):
        limit = 15
        start = time()
        question = choice(list(self.geo_questions.keys()))
        imgreg = re.search("https.*png", question)
        answers = [str(x).lower() for x in self.geo_questions[question]]
        embed = discord.Embed(title="GEOGRAPHY CHALLENGE", description=f"You have {limit} seconds to answer the following question:\n\n`{question.replace(imgreg.group(), '') if imgreg else question}`", colour=discord.Color.teal())
        embed.set_footer(text="Letter case doesn't matter.")
        if imgreg:
            embed.set_image(url=imgreg.group())
        message = await self.bf_data["channel"].send(embed=embed)
        def check(m):
            return not m.author.bot and m.content.lower() in answers and m.channel == self.bf_data["channel"]
        success = []
        while time() - start < limit:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=3)
                if msg.author not in success:
                    success.append(msg.author)
            except TimeoutError:
                pass
        await message.edit(embed=discord.Embed(title="GEOGRAPHY CHALLENGE", description=f"The right answer was `{answers[0].upper()}`", colour=discord.Color.dark_teal()))
        await message.delete(delay=5) 
        return success
                            
    async def trivia_chall(self):
        limit = 15
        start = time()
        question = choice(list(self.trivia_questions.keys()))
        answers = [str(x).lower() for x in self.trivia_questions[question]]
        embed = discord.Embed(title="TRIVIA CHALLENGE", description=f"You have {limit} seconds to answer the following question:\n\n`{question}`", colour=discord.Color.orange())
        embed.set_footer(text="Letter case doesn't matter.")
        message = await self.bf_data["channel"].send(embed=embed)
        def check(m):
            return not m.author.bot and m.content.lower() in answers and m.channel == self.bf_data["channel"]
        success = []
        while time() - start < limit:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=3)
                if msg.author not in success:
                    success.append(msg.author)
            except TimeoutError:
                pass
        await message.edit(embed=discord.Embed(title="TRIVIA CHALLENGE", description=f"The right answer was `{answers[0].upper()}`", colour=discord.Color.dark_orange()))
        await message.delete(delay=5) 
        return success
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and self.bf_active and message.channel == self.bf_data["channel"]:
            await message.delete()
        
    @commands.guild_only()
    @commands.is_owner()   
    @commands.command()
    async def bosshp(self, ctx, hp:int):
        await self.config.boss_hp.set(hp)
        await ctx.send(f"Boss HP set to {hp}")
    
    @commands.is_owner()   
    @commands.command()
    async def bossfight(self, ctx, channel:discord.TextChannel):
        if self.bf_active:
            return await ctx.send("Boss Fight is already running!")
        self.bf_data = {
                "channel" : channel,
                "message" : None,
                "embed" : None,
                "hp_left" : await self.config.boss_hp(),
                "players" : {}
                }
        self.bf_active = True 
        embed = discord.Embed(title="BOSS FIGHT", colour=discord.Colour.red())
        embed.set_thumbnail(url="https://i.imgur.com/HWjZtEP.png")
        embed.add_field(name=f"{self.HP_EMOJI} HP Left", value=f"{self.bf_data['hp_left']}/{await self.config.boss_hp()}", inline=False)
        embed.add_field(name=f"{self.WAITING_EMOJI} Starting in:", value=f"{self.START_WAIT_TIME} seconds!")

        main_message = await channel.send(embed=embed)
        self.bf_data["message"] = main_message           
        await sleep(self.START_WAIT_TIME)

        embed.set_field_at(1, name="Action log:", value="Boss Fight started!")
        #embed.set_footer(text="")
        await self.bf_data["message"].edit(embed=embed)
        self.bf_data["embed"] = embed
        await self.main_loop()
                        
    @commands.command()
    async def bosfight(self, ctx, channel:discord.TextChannel):
        self.bf_active = True
        embed = discord.Embed(title="BOSS FIGHT", colour=discord.Colour.red())
        embed.set_thumbnail(url="https://i.imgur.com/HWjZtEP.png")
        embed.add_field(name=f"{self.HP_EMOJI} HP Left", value=f"10000/10000", inline=False)
        embed.add_field(name=f"{self.WAITING_EMOJI} Starting in:", value=f"60 seconds!")
        message = await channel.send(embed=embed)
        self.bf_data = {"channel" : channel, "message" : message}
        await sleep(60)
                        
        embed.set_field_at(1, name="Action log:", value="Boss Fight started!")
        await self.bf_data["message"].edit(embed=embed)
        self.bf_data["embed"] = embed
        await sleep(5)
                        
        membed = discord.Embed(title="MATH CHALLENGE", description=f"You have 15 seconds to write a result of:\n\n`2 + 2 - 1`", colour=discord.Color.magenta())
        membed.set_footer(text="Do not use calculator!")
        math = await self.bf_data["channel"].send(embed=membed)
        await sleep(15)
        await math.delete()
        rembed = discord.Embed(title="RIGHT ANSWER", colour=discord.Colour.green())
        rembed.set_image(url="https://i.imgflip.com/1wg0hg.jpg")
        msg = await self.bf_data["channel"].send(embed=rembed)
        
                        
        embed = self.bf_data["embed"]
        embed.set_field_at(0, name=f"{self.HP_EMOJI} HP Left", value=f"100069/100000", inline=False)
        embed.set_field_at(1, name=f"{self.LOG_EMOJI} Action log:", value="You all got it wrong!")
        await self.bf_data["message"].edit(embed=embed)
        await sleep(10)
        await msg.delete()
                        
        gembed = discord.Embed(title="GEOGRAPHY CHALLENGE", description=f"You have 15 seconds to answer the following question:\n\n`Where is LA?`", colour=discord.Color.teal())
        geo = await self.bf_data["channel"].send(embed=gembed)
        await sleep(15)
        await geo.delete()
        rembed = discord.Embed(title="RIGHT ANSWER", colour=discord.Colour.green())
        rembed.set_image(url="https://i.imgur.com/ABCrXwE.jpg")
        msg = await self.bf_data["channel"].send(embed=rembed)
                        
        embed = self.bf_data["embed"]
        embed.set_field_at(0, name=f"{self.HP_EMOJI} HP Left", value=f"42/100000", inline=False)
        embed.set_field_at(1, name=f"{self.LOG_EMOJI} Action log:", value="You all have no brains!")
        await self.bf_data["message"].edit(embed=embed)
        await sleep(10)
        await msg.delete()
                        
        tembed = discord.Embed(title="TYPING CHALLENGE", description=f"You have 2 seconds to type the following word(s):\n\n`Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.`", colour=discord.Color.orange())
        ty = await self.bf_data["channel"].send(embed=tembed)
        await sleep(15)
        await ty.delete()
                        
        embed = self.bf_data["embed"]
        embed.set_field_at(0, name=f"{self.HP_EMOJI} HP Left", value=f"1000000000000/100000", inline=False)
        embed.set_field_at(1, name=f"{self.LOG_EMOJI} Action log:", value="Can you not write? You all are so lame hahahahaha")
        await self.bf_data["message"].edit(embed=embed)
        await sleep(10)
                        
        than = discord.Embed(colour=discord.Colour.red())
        than.set_image(url="https://media.giphy.com/media/3oxHQqHQ5zzkrQ4VfW/giphy.gif")
        tha = await self.bf_data["channel"].send(embed=than)
        await sleep(15)
        await tha.delete()
        than2 = discord.Embed(colour=discord.Colour.red())
        than2.set_image(url="https://media.tenor.com/images/4ce724176ca3f2f85076db5dc342781c/tenor.gif")
        tha2 = await self.bf_data["channel"].send(embed=than2)
        await sleep(15)
        await tha2.delete()
        than3 = discord.Embed(colour=discord.Colour.red())
        than3.set_image(url="https://media.tenor.com/images/c9e8c807b43a11b530d551ff36376ffe/tenor.gif")
        tha3 = await self.bf_data["channel"].send(embed=than3)
        await sleep(15)
        await tha3.delete()
        embed = self.bf_data["embed"]
        embed.set_thumbnail(url="https://i.imgur.com/fo3Tqfd.png")
        embed.set_field_at(0, name=f"{self.HP_EMOJI} HP Left", value=f"-426925252525/0", inline=False)
        embed.set_field_at(1, name=f"{self.LOG_EMOJI} Action log:", value="Boss has been defeated!")
        embed.set_footer(text="Happy April Fools!")
        await self.bf_data["message"].edit(embed=embed)
        await self.bf_data["channel"].send(embed=discord.Embed(title="Damage leaderboard", description="THANOS <:damage:643539221428174849> `426925252525`\n", colour=discord.Colour.gold()))
        self.bf_active = False
