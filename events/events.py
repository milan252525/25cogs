import discord
from redbot.core import commands, Config, checks
from discord.ext import tasks
from asyncio import sleep
from random import choice, randint

class Events(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        #self.config = Config.get_conf(self, identifier=25993325)
        #default_member = {"bossfight" : {"damage_dealt" : 0, "powercubes" : 0}}
        #self.config.register_member(**default_member)
        self.data = {
            "bossfight" : {
                "active" : False,
                "channel" : None,
                "message" : None,
                "embed" : None,
                "hp_left" : 5000
                }
            }
        self.actions = []
        self.players = {}

    @tasks.loop(seconds=20)
    async def messageupdateloop(self):
        new_actions_str = ""
        for action in self.actions:
            if action[0] == "D":
                new_actions_str += f"{action[1]} -{action[2]} HP\n"
                self.data["bossfight"]["hp_left"] -= action[2]
                damage += action[2]
            elif action[0] == "P":
                new_actions_str += f"{action[1]} collected a power cube ({action[2]})\n"
        self.actions = []
        embed = self.data["bossfight"]["embed"]
        embed.set_field_at(0, name="HP Left", value=f"{self.data['bossfight']['hp_left']}/5000", inline=False)
        embed.set_field_at(1, name="Action log:", value="Boss Fight started!")
        await self.data["bossfight"]["message"].edit(embed=embed)


    @tasks.loop(seconds=10)
    async def randomspawnloop(self):
        rand = randint(0,10)
        if rand < 5:
            await self.spawn_cube()

    # @tasks.loop(seconds=20)
    # async def randomkillloop(self):
    #     print()
        
    async def spawn_cube(self):
        embed = discord.Embed(description="<:powercube:643517745199054855> Power cube spawned!\nPick it up by reacting!", colour=discord.Color.green())
        message = await self.data["bossfight"]["channel"].send(embed=embed)
        message.add_reaction("<:powercube:643517745199054855>")
        def check(reaction, user):
                return str(reaction.emoji) == "<:powercube:643517745199054855>"
        _, user = await self.bot.wait_for('reaction_add', check=check)
        if user.id not in self.players.keys():
                self.players[user.id] = {"damage" : 0, "power_cubes" : 0}
        self.players[user.id]["power_cubes"] += 1
        await message.edit(embed=discord.Embed(description=f"<:powercube:643517745199054855> {user.mention} collected the power cube!\nCurrent amount: {self.players[user.id]['power_cubes']}", colour=discord.Color.green()))
        self.actions.append("P", [message.author.mention, self.players[message.author.id]["power_cubes"]])
        await message.delete(delay=3)

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.data["bossfight"]["active"] and message.channel == self.data["bossfight"]["channel"]:
            if message.author.id not in self.players.keys():
                self.players[message.author.id] = {"damage" : 0, "power_cubes" : 0}
            self.actions.append("D", [message.author.mention, (self.players[message.author.id]["power_cubes"] + 1) * 100])
            await message.delete(delay=1)
            
        
    @commands.guild_only()
    @commands.is_owner()   
    @commands.command()
    async def bossfight(self, ctx, channel:discord.TextChannel):
        self.data["bossfight"]["channel"] = channel
        self.data["bossfight"]["active"] = True

        embed = discord.Embed(title="BOSS FIGHT", colour=discord.Colour.red())
        embed.set_thumbnail(url="https://i.imgur.com/fo3Tqfd.png")
        embed.add_field(name="HP Left", value=f"{self.data['bossfight']['hp_left']}/5000", inline=False)
        embed.add_field(name="Starting in:", value="5 seconds")
        
        main_message = await channel.send(embed=embed)
        self.data["bossfight"]["message"] = main_message
        self.data["bossfight"]["embed"] = embed

        sleep(5)

        embed.set_field_at(1, name="Action log:", value="Boss Fight started!")
        self.data["bossfight"]["message"].edit(embed=embed)

        self.messageupdateloop.start()
        self.randomspawnloop.start()