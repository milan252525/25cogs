import discord
from redbot.core import commands, Config, checks
from redbot.core.utils.embed import randomize_colour
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from random import choice
import time
import math

class Ladder(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=25171725)
        default_member = {
            "wins" : 0,
            "losses" : 0,
            "last_played" : None,
            "win_streak" : 0,
            "longest_win_streak" : 0,
            "highest_rank": None,
            "name" : None,
            "match_history" : [],
            "registered" : None,
            "elo" : 1200
        }
        self.config.register_member(**default_member)
        # default_guild = {"leaderboard" : []}
        # self.config.register_guild(**default_guild)

    def calculate_elo(self, old_rating_player_a : int, old_rating_player_b : int, win : bool):
        expected = 1 / (1 + math.pow(10, (-((old_rating_player_a - old_rating_player_b)/400))))
        actual = 1 if win else 0
        return old_rating_player_a + 30 * (actual - expected)

        
    @commands.guild_only()
    @commands.group(aliases=["lb", "ladder"], invoke_without_command=True)
    async def leaderboard(self, ctx):
        await ctx.send("LADDER")

    @commands.guild_only()
    @commands.group(aliases=["r", "reg"], invoke_without_command=True, name="register")
    async def leaderboard_register(self, ctx, member : discord.Member = None):
        if member != None and not ctx.author.server_permissions.administrator:
            embed = discord.Embed(colour = discord.Colour.red(), description = "Only administrators can register other players!")
            return await ctx.send(embed = embed)
        member = ctx.author if member == None else member
        await self.config.member(member).name.set(member.display_name)
        await self.config.member(member).registered.set(int(time.time()))
        await ctx.send(f"{member.mention} was successfully registered")
        