import discord
from redbot.core import commands, Config, checks
from redbot.core.data_manager import cog_data_path
from discord.ext import tasks
from asyncio import sleep, TimeoutError, ensure_future, get_event_loop
from random import choice, randint, sample
from copy import copy
from time import time
import yaml
import re


class Events(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=2567124825)
        self.config.register_global(
            boss_hp=10000
        )
        default_user = {"boss_fight": {"damage" : 0, "participated" : 0}}
        self.config.register_member(**default_user)
        self.DAMAGE_PER_CHALL = 200
        self.START_WAIT_TIME = 60
        #self.DAMAGE_EMOJI = "<:damage:643539221428174849>"
        self.DAMAGE_EMOJI = "💥"
        self.HP_EMOJI = "<:health:688109898508009611>"
        self.LOG_EMOJI = "<:log:688112584368586779>"
        self.WAITING_EMOJI = "<:dyna:688120749323845637>"
        self.bf_data = None
        self.bf_active = False
        with open(str(cog_data_path(self)).replace("Events", r"CogManager/cogs/events/geo.yaml")) as file:
            self.geo_questions = yaml.load(file, Loader=yaml.FullLoader)
        with open(str(cog_data_path(self)).replace("Events", r"CogManager/cogs/events/trivia.yaml")) as file:
            self.trivia_questions = yaml.load(file, Loader=yaml.FullLoader)
        # with open(str(cog_data_path(self)).replace("Events", r"CogManager/cogs/events/longwords.txt")) as file:
        #     self.longwords = []
        #     line = file.readline()
        #     while line != "":
        #         self.longwords.append(line.replace("\n", ""))
        #         line = file.readline()
        with open(str(cog_data_path(self)).replace("Events", r"CogManager/cogs/events/shufflewords.txt")) as file:
            self.shufflewords = []
            line = file.readline()
            while line != "":
                self.shufflewords.append(line.replace("\n", ""))
                line = file.readline()
        self.bscog = bot.get_cog("BrawlStarsCog")
        self.brawlers = None

    async def main_loop(self):
        while self.bf_data['hp_left'] > 0:
            chall = choice(("word", "math", "geo", "trivia", "brawl", "word", "math", "brawl"))
            
            chance = randint(0, 100)
            only_first_five = False
            if chance < 20:
                only_first_five = True
                embed = discord.Embed(title="BOSS GOT ANGRY", description=f"Next challenge accepts only first **5** right answers!", colour=discord.Color.red())
                embed.set_footer(text="Be quick!")
                message = await self.bf_data["channel"].send(embed=embed)
                await sleep(5)
                await message.delete()

            boss_kill = False
            dead = []
            if not only_first_five and chance < 30 and len(self.bf_data["players"]) > 0:
                hit = ""
                boss_kill = True
                for _ in range(randint(1, (len(self.bf_data["players"])//5)+2)):
                    to_kill = choice(list(self.bf_data["players"].keys()))
                    if to_kill not in dead:
                        dead.append(to_kill)
                hit = " ".join([self.bot.get_user(x).mention for x in dead])
                embed = discord.Embed(title="BOSS LAUNCHED A MISSILE", description=f"Following players got hit and can't answer this round:\n{hit}", colour=discord.Color.red())
                embed.set_footer(text="Better luck next time!")
                message = await self.bf_data["channel"].send(embed=embed)
                await sleep(10)
                await message.delete()

            #start random challenge
            if chall == "word":
                res = await self.word_chall()
            elif chall == "math":
                res = await self.math_chall()
            elif chall == "geo":
                res = await self.geo_chall()
            elif chall == "trivia":
                res = await self.trivia_chall()
            elif chall == "brawl":
                res = await self.brawler_chall()
            
            #process results
            if only_first_five:
                res = res[:5]
            if boss_kill:
                for d in dead:
                    to_kill = self.bot.get_user(d)
                    if to_kill in res:
                        res.remove(to_kill)

            damage = 0
            log = ""
            dealt = self.DAMAGE_PER_CHALL
            for m in res:
                damage += dealt
                log += f"{self.DAMAGE_EMOJI}{m.display_name} `{dealt}`\n"
                if m.id not in self.bf_data["players"]:
                    self.bf_data["players"][m.id] = dealt
                else:
                    self.bf_data["players"][m.id]  += dealt
                dealt = (dealt - 5) if dealt > 150 else dealt
            log = "Noone was successful!" if log == "" else log
            self.bf_data['hp_left'] -= damage
            #update action log
            if len(log) > 1000:
                log = log[:1000] + "\n... (ommited)"
            embed = self.bf_data["embed"]
            embed.set_field_at(0, name=f"{self.HP_EMOJI} HP Left", value=f"{self.bf_data['hp_left']}/{await self.config.boss_hp()}", inline=False)
            embed.set_field_at(1, name=f"{self.LOG_EMOJI} Action log:", value=log)
            embed.set_footer(text="Send answers to LA Bot as a direct message")
            await self.bf_data["message"].edit(embed=embed)
            if self.bf_data['hp_left'] > 0:
                await sleep(15)

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
            if len(msg) > 1850:
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
            limit = 10
            num1, num2 = randint(10, 500), randint(30, 500)
            result = num1 + num2
        elif op == "-":
            limit = 10
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
            num1 = randint(1, 30) * num2
            result = num1 // num2
                               
        embed = discord.Embed(title="MATH CHALLENGE", description=f"You have {limit} seconds to write a result of:\n\n`{num1} {op} {num2}`", colour=discord.Color.magenta())
        embed.set_footer(text="ANSWER IN DM. Do not use calculator!")
        message = await self.bf_data["channel"].send(embed=embed)
        def check(m):
            return not m.author.bot and str(result) in m.content.lower() and isinstance(m.channel, discord.abc.PrivateChannel) and m.author in self.bf_data["channel"].guild.members
        success = []
        while time() - start < limit:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=3)
                if msg.author not in success:
                    success.append(msg.author)
            except TimeoutError:
                pass
        await message.edit(embed=discord.Embed(title="MATH CHALLENGE", description=f"The right answer was `{result}`", colour=discord.Color.dark_magenta()))
        await message.delete(delay=10)
        return success
        
    async def word_chall(self):
        word = choice(self.shufflewords)
        shuffled = ''.join(sample(word, len(word)))
        limit = 15
        start = time()
        embed = discord.Embed(title="UNSCRAMBLE CHALLENGE", description=f"You have {limit} seconds to unscramble:\n\n`{shuffled.upper()}`", colour=discord.Color.blue())
        embed.set_footer(text="ANSWER IN DM. Words are BS themed.")
        message = await self.bf_data["channel"].send(embed=embed)
        def check(m):
            return not m.author.bot and word in m.content.lower() and isinstance(m.channel, discord.abc.PrivateChannel) and m.author in self.bf_data["channel"].guild.members
        success = []
        while time() - start < limit:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=3)
                if msg.author not in success:
                    success.append(msg.author)
            except TimeoutError:
                pass
        await message.edit(embed=discord.Embed(title="UNSCRAMBLE CHALLENGE", description=f"The right answer was `{word}`", colour=discord.Color.blue()))
        await message.delete(delay=10) 
        return success
 
    async def geo_chall(self):
        limit = 15
        start = time()
        question = choice(list(self.geo_questions.keys()))
        imgreg = re.search("https.*png", question)
        answers = [str(x).lower() for x in self.geo_questions[question]]
        embed = discord.Embed(title="GEOGRAPHY CHALLENGE", description=f"You have {limit} seconds to answer the following question:\n\n`{question.replace(imgreg.group(), '') if imgreg else question}`", colour=discord.Color.teal())
        embed.set_footer(text="ANSWER IN DM.")
        if imgreg:
            embed.set_image(url=imgreg.group())
        message = await self.bf_data["channel"].send(embed=embed)
        def check(m):
            return not m.author.bot and m.content.lower() in answers and isinstance(m.channel, discord.abc.PrivateChannel) and m.author in self.bf_data["channel"].guild.members
        success = []
        while time() - start < limit:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=3)
                if msg.author not in success:
                    success.append(msg.author)
            except TimeoutError:
                pass
        await message.edit(embed=discord.Embed(title="GEOGRAPHY CHALLENGE", description=f"The right answer was `{answers[0].upper()}`", colour=discord.Color.dark_teal()))
        await message.delete(delay=10) 
        return success
                            
    async def trivia_chall(self):
        limit = 15
        start = time()
        question = choice(list(self.trivia_questions.keys()))
        answers = [str(x).lower() for x in self.trivia_questions[question]]
        embed = discord.Embed(title="TRIVIA CHALLENGE", description=f"You have {limit} seconds to answer the following question:\n\n`{question}`", colour=discord.Color.orange())
        embed.set_footer(text="ANSWER IN DM. Letter case doesn't matter.")
        message = await self.bf_data["channel"].send(embed=embed)
        def check(m):
            return not m.author.bot and m.content.lower() in answers and isinstance(m.channel, discord.abc.PrivateChannel) and m.author in self.bf_data["channel"].guild.members
        success = []
        while time() - start < limit:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=3)
                if msg.author not in success:
                    success.append(msg.author)
            except TimeoutError:
                pass
        await message.edit(embed=discord.Embed(title="TRIVIA CHALLENGE", description=f"The right answer was `{answers[0].upper()}`", colour=discord.Color.dark_orange()))
        await message.delete(delay=10) 
        return success

    async def brawler_chall(self):
        limit = 15
        start = time()
        brawler = choice(self.brawlers['list'])
        key = choice(("starPowers", "gadgets"))
        to_guess = choice(brawler[key])
        answer = brawler['name']
        embed = discord.Embed(title="BRAWLER CHALLENGE", description=f"You have {limit} seconds to answer the following question:\n\n`What brawler has Star Power/Gadget called {to_guess['name']}?`", colour=discord.Color.green())
        embed.set_footer(text="ANSWER IN DM. Letter case doesn't matter.")
        message = await self.bf_data["channel"].send(embed=embed)
        def check(m):
            return not m.author.bot and answer.lower() in m.content.lower() and isinstance(m.channel, discord.abc.PrivateChannel) and m.author in self.bf_data["channel"].guild.members
        success = []
        while time() - start < limit:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=3)
                if msg.author not in success:
                    success.append(msg.author)
            except TimeoutError:
                pass
        await message.edit(embed=discord.Embed(title="BRAWLER CHALLENGE", description=f"The right answer was `{answer}`", colour=discord.Color.dark_green ()))
        await message.delete(delay=10)
        return success
    
    #@commands.Cog.listener()
    async def disabled_on_message(self, message):
        if not message.author.bot and self.bf_active and message.channel == self.bf_data["channel"]:
            await message.delete()
    
    @commands.has_role("Manager") 
    @commands.guild_only()  
    @commands.command()
    async def bosshp(self, ctx, hp:int):
        await self.config.boss_hp.set(hp)
        await ctx.send(f"Boss HP set to {hp}")
    
    @commands.has_role("Manager")   
    @commands.command()
    async def bossfight(self, ctx, channel:discord.TextChannel):
        if self.bf_active:
            return await ctx.send("Boss Fight is already running!")
        if self.brawlers is None:
            self.brawlers = await self.bscog.starlist_request("https://api.starlist.pro/brawlers")
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
