import discord
from redbot.core import commands, Config, checks
from discord.ext import tasks
from asyncio import sleep
from random import choice, randint
from copy import deepcopy

class Events(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        #self.config = Config.get_conf(self, identifier=25993325)
        #default_member = {"bossfight" : {"damage_dealt" : 0, "powercubes" : 0}}
        #self.config.register_member(**default_member)
        self.BOSS_HP = 5000
        self.DAMAGE_PER_CUBE = 100
        self.DEFAULT_DATA = {
            "bossfight" : {
                "active" : False,
                "channel" : None,
                "message" : None,
                "embed" : None,
                "hp_left" : self.BOSS_HP
                }
            }
        self.data = deepcopy(self.DEFAULT_DATA)
        self.actions = []
        self.players = {}
        

    def cog_unload(self):
        self.messageupdateloop.cancel()
        self.randomspawnloop.cancel()

    @tasks.loop(seconds=15)
    async def messageupdateloop(self):
        new_actions_str = ""
        for action in self.actions:
            if action[0] == "D":
                new_actions_str += f"{action[1]} -{action[2]} HP\n"
                self.data["bossfight"]["hp_left"] -= action[2]
            elif action[0] == "P":
                new_actions_str += f"{action[1]} collected a power cube ({action[2]})\n"
            if action[0] == "3D":
                new_actions_str += f"{action[1]} -{action[2]} HP **(x3)**\n"
                self.data["bossfight"]["hp_left"] -= action[2]
        self.actions = []
        if len(new_actions_str) == 0:
            new_actions_str = "Deal damage by sending messages!"
        if self.data["bossfight"]["hp_left"] <= 0:
            await self.finish()
        else:
            embed = self.data["bossfight"]["embed"]
            embed.set_field_at(0, name="HP Left", value=f"{self.data['bossfight']['hp_left']}/{self.BOSS_HP}", inline=False)
            embed.set_field_at(1, name="Action log:", value=new_actions_str)
            await self.data["bossfight"]["message"].edit(embed=embed)


    @tasks.loop(seconds=15)
    async def randomspawnloop(self):
        rand = randint(1,10)
        if rand < 4:
            await self.spawn_cube()
        elif rand < 8:
            await self.spawn_challenge()

    # @tasks.loop(seconds=20)
    # async def randomkillloop(self):
    #     print()

    async def finish(self):
        self.messageupdateloop.cancel()
        self.randomspawnloop.cancel()
        self.data["bossfight"]["active"] = False
        embed = self.data["bossfight"]["embed"]
        embed.set_field_at(0, name="HP Left", value=f"0/{self.BOSS_HP}", inline=False)
        embed.set_field_at(1, name="Action log:", value="Boss was defeated!")
        embed.set_footer(text=discord.Embed.Empty)
        await self.data["bossfight"]["message"].edit(embed=embed)
        final = []
        for k in self.players.keys():
            final.append([k, self.players[k]["damage"], self.players[k]["power_cubes"]])
        final.sort(key=lambda x: x[1], reverse=True)
        msg = ""
        messages = []
        for p in final:
            if len(msg) > 1500:
                messages.append(msg)
                msg = ""
            u = self.bot.get_user(p[0])
            msg += f"{u.mention} <:damage:643539221428174849> `{p[1]}` <:powercube:643517745199054855> `{p[2]}`\n"
        if len(msg) > 0:
            messages.append(msg)
        for m in messages:
            await self.data["bossfight"]["channel"].send(embed=discord.Embed(description=m, colour=discord.Colour.gold()))
        self.data = deepcopy(self.DEFAULT_DATA)
        self.actions = []
        self.players = {}
        
    async def spawn_cube(self):
        embed = discord.Embed(description="<:powercube:643517745199054855> Power cube spawned!\nPick it up by reacting!", colour=discord.Color.green())
        message = await self.data["bossfight"]["channel"].send(embed=embed)
        await message.add_reaction("<:powercube:643517745199054855>")
        def check(reaction, user):
                return str(reaction.emoji) == "<:powercube:643517745199054855>" and not user.bot
        _, user = await self.bot.wait_for('reaction_add', check=check)
        if user.id not in self.players.keys():
                self.players[user.id] = {"damage" : 0, "power_cubes" : 0}
        self.players[user.id]["power_cubes"] += 1
        await message.edit(embed=discord.Embed(description=f"<:powercube:643517745199054855> {user.mention} collected the power cube!\nCurrent amount: {self.players[user.id]['power_cubes']}", colour=discord.Color.green()))
        self.actions.append(["P", user.mention, self.players[user.id]["power_cubes"]])
        await message.delete(delay=3)

    async def spawn_challenge(self):
        word = choice(["shelly", "nita", "colt", "mortis", "bull", "bounty", "showdown"])
        embed = discord.Embed(description=f"<:sd:614517124219666453> Deal triple damage to the bot!\nType \"{word}\"!", colour=discord.Color.blue())
        message = await self.data["bossfight"]["channel"].send(embed=embed)
        def check(m):
            return not m.author.bot and word in m.content.lower() and m.channel == self.data["bossfight"]["channel"]
        msg = await self.bot.wait_for('message', check=check)
        if msg.author.id not in self.players.keys():
            self.players[msg.author.id] = {"damage" : 0, "power_cubes" : 0}
        damage = (self.players[msg.author.id]["power_cubes"] + 1) * self.DAMAGE_PER_CUBE * 3
        await message.edit(embed=discord.Embed(description=f"<:sd:614517124219666453> {msg.author.mention} dealt triple damage ({damage}) to the bot", colour=discord.Color.blue()))
        self.players[msg.author.id]["damage"] += damage
        self.actions.append(["3D", msg.author.mention, damage])
        await message.delete(delay=3)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and self.data["bossfight"]["active"] and message.channel == self.data["bossfight"]["channel"]:
            if message.author.id not in self.players.keys():
                self.players[message.author.id] = {"damage" : 0, "power_cubes" : 0}
            damage = (self.players[message.author.id]["power_cubes"] + 1) * self.DAMAGE_PER_CUBE
            self.players[message.author.id]["damage"] += damage
            self.actions.append(["D", message.author.mention, damage])
            await message.delete(delay=1)
            
        
    @commands.guild_only()
    @commands.is_owner()   
    @commands.command()
    async def bossfight(self, ctx, channel:discord.TextChannel):
        self.data["bossfight"]["channel"] = channel

        embed = discord.Embed(title="BOSS FIGHT", colour=discord.Colour.red())
        embed.set_thumbnail(url="https://i.imgur.com/fo3Tqfd.png")
        embed.add_field(name="HP Left", value=f"{self.data['bossfight']['hp_left']}/{self.BOSS_HP}", inline=False)
        embed.add_field(name="Starting in:", value="5 seconds")
        
        main_message = await channel.send(embed=embed)
        self.data["bossfight"]["message"] = main_message
        

        await sleep(5)

        embed.set_field_at(1, name="Action log:", value="Boss Fight started!")
        embed.set_footer(text="Damage boss by sending messages!")
        await self.data["bossfight"]["message"].edit(embed=embed)

        self.data["bossfight"]["embed"] = embed

        self.data["bossfight"]["active"] = True

        self.messageupdateloop.start()
        await sleep(5)
        self.randomspawnloop.start()