import discord
from redbot.core import commands, Config, checks
from discord.ext import tasks

class Events(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=25993325)
        default_global = {"bossfight" : {"active" : False, "channel" : None, "hp_left" : 0}}
        default_member = {"bossfight" : {"damage_dealt" : 0, "powercubes" : 0}}
        self.config.register_global(**default_global)
        self.config.register_member(**default_member)    

    @tasks.loop(seconds=15)
    async def bfloop(self):
        channel = self.bot.get_channel(await self.config.bossfight.channel())
        
    @commands.guild_only()
    @commands.is_owner()   
    @commands.command()
    async def bossfight(self, ctx, channel : discord.TextChannel):
        await self.config.bossfight.channel.set(channel.id)
        await self.config.bossfight.active.set(True)

        embed = discord.Embed(title = "BOSS FIGHT", colour = discord.Colour.red())
        embed.set_thumbnail(url = "https://i.imgur.com/fo3Tqfd.png")
        embed.add_field(name = "HP Left", value = f"100000/100000")
        embed.add_field(name = "Starting in:", value = "5 minutes")

        await channel.send(embed=embed)

        

