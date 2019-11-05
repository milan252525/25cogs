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
            "registered" : False,
            "id" : None, 
            "wins" : 0,
            "losses" : 0,
            "last_played" : None,
            "win_streak" : 0,
            "longest_win_streak" : 0,
            "highest_rank": None,
            "name" : None,
            "match_history" : [],
            "registered_time" : None,
            "elo" : 1200
        }
        self.config.register_member(**default_member)
        # default_guild = {"leaderboard" : []}
        # self.config.register_guild(**default_guild)

    #https://blog.mackie.io/the-elo-algorithm
    def calculate_elo(self, old_rating_player_a : int, old_rating_player_b : int, win : bool):
        expected = 1 / (1 + math.pow(10, (-((old_rating_player_a - old_rating_player_b)/400))))
        actual = 1 if win else 0
        return int(old_rating_player_a + 30 * (actual - expected))

    async def one_match_result(self, winner, loser):
        winner_elo = await self.config.member(winner).elo()
        loser_elo = await self.config.member(winner).elo()
        winner_new = self.calculate_elo(winner_elo, loser_elo, True)
        loser_new = self.calculate_elo(loser_elo, winner_elo, False)
        await self.config.member(winner).elo.set(winner_new)
        await self.config.member(winner).elo.set(loser_new)
        return winner_elo, winner_new, loser_elo, loser_new

    @commands.command(aliases=['p'])
    async def result(self, ctx, winner : discord.Member, loser : discord.Member):
        result = await self.one_match_result(winner, loser)
        embed = discord.Embed(colour = discord.Color.green())
        embed.add_field(name = "Winner", value = f"{winner.mention} {result[0]} -> {result[1]}")
        embed.add_field(name = "Loser", value = f"{loser.mention} {result[2]} -> {result[3]}")
        ctx.send(embed=embed)

    @commands.guild_only()
    @commands.group(aliases=["lb", "ladder"], invoke_without_command=True)
    async def leaderboard(self, ctx):
        players = await self.config.all_members(ctx.guild)
        values = []
        for k in players.keys():
            values.append([players[k]["elo"], players[k]["name"]])
        values.sort(key=lambda x: x[0])
        msg = ""
        for v in values:
            msg += f"{v[1]} `{v[0]}`\n"
        await ctx.send(embed = discord.Embed(colour = discord.Colour.blue(), description = msg))

    @commands.guild_only()
    @leaderboard.command(aliases=["r", "reg"], name="register")
    async def leaderboard_register(self, ctx, member : discord.Member = None):
        if member != None and not ctx.author.guild_permissions.administrator:
            return await ctx.send(embed = discord.Embed(colour = discord.Colour.red(), description = "Only administrators can register other players!"))
        member = ctx.author if member == None else member
        if await self.config.member(member).registered():
            return await ctx.send(embed = discord.Embed(colour = discord.Colour.red(), description = f"{member.mention} is already registered!"))
        await self.config.member(member).registered.set(True)
        await self.config.member(member).name.set(member.display_name)
        await self.config.member(member).id.set(member.id)
        await self.config.member(member).registered_time.set(int(time.time()))
        await self.config.member(member).wins.set(await self.config.member(member).wins() + 1)
        await ctx.send(embed = discord.Embed(colour = discord.Colour.green(), description = f"{member.mention} was successfully registered"))
        