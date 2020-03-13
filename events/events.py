import discord
from redbot.core import commands, Config, checks
from discord.ext import tasks
from asyncio import sleep, TimeoutError
from random import choice, randint
from copy import copy
from time import time

class Events(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.BOSS_HP = 1000
        self.DAMAGE_PER_CHALL = 200
        self.START_WAIT_TIME = 5
        self.DAMAGE_EMOJI = "<:damage:643539221428174849>"
        self.bf_data = None
        self.bf_active = False

    async def main_loop(self):
        while self.bf_data['hp_left'] > 0:
            chall = choice(("word", "math"))
            #start random challenge
            if chall == "word":
                res = await self.word_chall()
            elif chall == "math":
                res = await self.math_chall()
            #process results
            damage = 0
            log = "BOOM!:\n"
            for m in res:
                damage += {self.DAMAGE_PER_CHALL}
                log += f"{self.DAMAGE_EMOJI}{m.display_name}"
                if m.id not in self.bf_data["players"]:
                    self.bf_data["players"][m.id] = self.DAMAGE_PER_CHALL
                else:
                    self.bf_data["players"][m.id] += self.DAMAGE_PER_CHALL
            self.bf_data['hp_left'] -= damage
            #update action log
            embed = self.bf_data["embed"]
            embed.set_field_at(0, name="HP Left", value=f"{self.bf_data['hp_left']}/{self.BOSS_HP}", inline=False)
            embed.set_field_at(1, name="Action log:", value=log)
            await self.bf_data["message"].edit(embed=embed)
            sleep(5)

        #finish
        embed = self.bf_data["embed"]
        embed.set_field_at(0, name="HP Left", value=f"0/{self.BOSS_HP}", inline=False)
        embed.set_field_at(1, name="Action log:", value="Boss has been defeated!")
        embed.set_footer(text="Let's party!")
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
            u = self.bot.get_user(p[0])
            msg += f"{u.mention} <:damage:643539221428174849> `{p[1]}`\n"
        if len(msg) > 0:
            messages.append(msg)
        for m in messages:
            await self.bf_data["channel"].send(embed=discord.Embed(description=m, colour=discord.Colour.gold()))
        self.bf_active = False
            
    async def math_chall(self):
        limit = 10
        start = time()
        num1 = randint(1, 50)
        num2 = randint(1, 50)
        result = num1 + num2
        embed = discord.Embed(description=f"You have {limit} seconds to write a result of:\n`{num1} + {num2}`", colour=discord.Color.blue())
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
        await message.delete(delay=1)
        return success
        
    async def word_chall(self):
        limit = 10
        start = time()
        word = choice(["duo showdown", "brawl stars", "brawl ball", "legendary alliance"])
        embed = discord.Embed(description=f"You have {limit} seconds to type:\n`{word}`", colour=discord.Color.blue())
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
        await message.delete(delay=1) 
        return success
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and self.bf_active and message.channel == self.bf_data["channel"]:
            await message.delete(delay=1)
        
    @commands.guild_only()
    @commands.is_owner()   
    @commands.command()
    async def bossfight(self, ctx, channel:discord.TextChannel):
        if self.bf_active:
            return await ctx.send("Boss Fight is already running!")
        self. bf_data = {
                "channel" : None,
                "message" : None,
                "embed" : None,
                "hp_left" : self.BOSS_HP,
                "players" : {}
                }
        self.bf_active = True                            
        self.bf_data["channel"] = channel

        embed = discord.Embed(title="LA BOSS FIGHT", colour=discord.Colour.red())
        embed.set_thumbnail(url="https://i.imgur.com/fo3Tqfd.png")
        embed.add_field(name="HP Left", value=f"{self.bf_data['hp_left']}/{self.BOSS_HP}", inline=False)
        embed.add_field(name="Starting in:", value=f"{self.START_WAIT_TIME} seconds")
        
        main_message = await channel.send(embed=embed)
        self.bf_data["message"] = main_message           
        await sleep(self.START_WAIT_TIME)

        embed.set_field_at(1, name="Action log:", value="Boss Fight started!")
        #embed.set_footer(text="")
        await self.bf_data["message"].edit(embed=embed)
        self.bf_data["embed"] = embed
        await self.main_loop()
