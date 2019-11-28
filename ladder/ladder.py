import discord
from redbot.core import commands, Config
from redbot.core.utils.mod import is_admin_or_superior
from redbot.core.utils.embed import randomize_colour
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from random import choice
import time
from datetime import datetime
import math

class Ladder(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=25171725)
        self.ELO_DEFAULT_VALUE = 1500
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
            "match_history" : {},
            "registered_time" : None,
            "elo" : self.ELO_DEFAULT_VALUE
        }
        self.config.register_member(**default_member)
        

    def badEmbed(self, text):
        bembed = discord.Embed(color=0xf50707)
        bembed.set_author(name=text, icon_url="https://i.imgur.com/dgE1VCm.png")
        return bembed
        
    def goodEmbed(self, text):
        gembed = discord.Embed(color=0x19d615)
        gembed.set_author(name=text, icon_url="https://i.imgur.com/fSAGoHh.png")
        return gembed

    #https://blog.mackie.io/the-elo-algorithm
    def calculate_elo(self, old_rating_player_a : int, old_rating_player_b : int, win : bool):
        expected = 1 / (1 + math.pow(10, (-((old_rating_player_a - old_rating_player_b)/400))))
        actual = 1 if win else 0
        return round(old_rating_player_a + 60 * (actual - expected))

    async def one_match_result(self, winner, loser):
        winner_elo = await self.config.member(winner).elo()
        loser_elo = await self.config.member(loser).elo()
        winner_new = self.calculate_elo(winner_elo, loser_elo, True)
        loser_new = self.calculate_elo(loser_elo, winner_elo, False)
        #elo
        await self.config.member(winner).elo.set(winner_new)
        await self.config.member(loser).elo.set(loser_new)
        #stats
        await self.config.member(winner).wins.set(await self.config.member(winner).wins() + 1)
        await self.config.member(loser).losses.set(await self.config.member(loser).losses() + 1)

        await self.config.member(winner).last_played.set(int(time.time()))
        await self.config.member(loser).last_played.set(int(time.time()))

        await self.config.member(winner).win_streak.set(await self.config.member(winner).win_streak() + 1)
        await self.config.member(loser).win_streak.set(0)

        if await self.config.member(winner).win_streak() > await self.config.member(winner).longest_win_streak():
            await self.config.member(winner).longest_win_streak.set(await self.config.member(winner).win_streak())

        await self.config.member(winner).set_raw("match_history", int(time.time()), value = {"opponent" : loser.id, "win" : True, "elo_old" : winner_elo, "elo_new" : winner_new})
        await self.config.member(loser).set_raw("match_history", int(time.time()), value = {"opponent" : winner.id, "win" : False, "elo_old" : loser_elo, "elo_new" : loser_new})
        
        return winner_elo, winner_new, loser_elo, loser_new

     

    @commands.command(aliases=["report"])
    async def result(self, ctx, winner : discord.Member, loser : discord.Member):
        """
        Report a result of a match

        Order of winner and loser is important!
        """
        if not await self.config.member(winner).registered():
            return await ctx.send(embed = self.badEmbed(f"{winner.display_name} is not registered! Use {ctx.prefix}lb register"))
        if not await self.config.member(loser).registered():
            return await ctx.send(embed = self.badEmbed(f"{loser.display_name} is not registered! Use {ctx.prefix}lb register"))
        result = await self.one_match_result(winner, loser)
        embed = discord.Embed(colour = discord.Color.green())
        embed.add_field(name = "Winner", value = f"{winner.mention} `{result[0]}` > `{result[1]}` (`+{result[1] - result[0]}`)", inline = False)
        embed.add_field(name = "Loser", value = f"{loser.mention} `{result[2]}` > `{result[3]}` (`{result[3] - result[2]}`)", inline = False)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.group(aliases=["lb", "ladder"], invoke_without_command=True)
    async def leaderboard(self, ctx):
        """
        View ELO leaderboard

        Register yourself using `/lb register`

        Report result of a match with `/result @winner @loser`

        Administrators are able to register other members
        `Example: /leaderboard register [member]`
        """
        players = await self.config.all_members(ctx.guild)
        values = []
        for k in players.keys():
            values.append([players[k]["elo"], self.bot.get_user(k).mention])
        values.sort(key=lambda x: x[0], reverse=True)
        msg = ""
        for v in values:
            msg += f"`{v[0]}` {v[1]}\n"
        await ctx.send(embed = discord.Embed(colour = discord.Colour.blue(), description = msg))

    @commands.guild_only()
    @leaderboard.command(aliases=["r", "reg"], name="register")
    async def leaderboard_register(self, ctx, member : discord.Member = None):
        """
        Register yourself to ELO leaderboard
        """
        if member != None and not ctx.author.guild_permissions.administrator:
            return await ctx.send(embed = self.badEmbed("Only administrators can register other players!"))
        member = ctx.author if member == None else member
        if await self.config.member(member).registered() or await self.config.member(member).elo() != self.ELO_DEFAULT_VALUE:
            return await ctx.send(embed = self.badEmbed(f"{member.display_name} is already registered!"))
        await self.config.member(member).registered.set(True)
        await self.config.member(member).name.set(member.display_name)
        await self.config.member(member).id.set(member.id)
        await self.config.member(member).registered_time.set(int(time.time()))
        await ctx.send(embed = self.goodEmbed(f"{member.display_name} was successfully registered"))
        
    @commands.guild_only()
    @commands.is_owner()
    @leaderboard.command(name="reset")
    async def leaderboard_reset(self, ctx):
        """
        Bot owner only command to reset leaderboard in a server
        ☢️DANGEROUS☢️
        """
        await self.config.clear_all_members(ctx.guild)
        await ctx.send(embed=self.goodEmbed("Successfully cleared all member data!"))

    @commands.guild_only()
    @leaderboard.command(name="setelo")
    async def leaderboard_setelo(self, ctx, member : discord.Member, new_elo : int):
        """
        Admin only command to set a specific member's ELO
        """
        if not is_admin_or_superior(self.bot, member):
            return await ctx.send(embed = self.badEmbed("Only administrators can set ELO!"))
        if not await self.config.member(member).registered():
            return await ctx.send(embed = self.badEmbed(f"{member.display_name} is not registered!"))
        await self.config.member(member).elo.set(new_elo)
        await ctx.send(embed=self.goodEmbed(f"{member.display_name}'s elo was set to {new_elo}"))

    @commands.guild_only()
    @leaderboard.command(name="stats")
    async def leaderboard_stats(self, ctx, member : discord.Member = None):
        """
        View someone's stats
        """
        member = ctx.author if member == None else member
        if not await self.config.member(member).registered():
            return await ctx.send(embed = self.badEmbed(f"{member.display_name} is not registered!"))
        embed = discord.Embed(colour = discord.Color.blue())
        embed.set_author(icon_url=member.avatar_url, name=f"{member.display_name}'s stats")
        embed.set_footer(text="All times are in UTC")
        embed.add_field(name="Current ELO", value=await self.config.member(member).elo(), inline=False)
        embed.add_field(name="Wins", value=await self.config.member(member).wins())
        embed.add_field(name="Losses", value=await self.config.member(member).losses())
        embed.add_field(name="Current Winstreak", value=await self.config.member(member).win_streak())
        embed.add_field(name="Longest Winstreak", value=await self.config.member(member).longest_win_streak())
        embed.add_field(name="Registration Date", value=datetime.fromtimestamp(await self.config.member(member).registered_time()).strftime("%d %B %H:%M"), inline=False)
        #embed.add_field(name="Last Played", value=datetime.fromtimestamp(await self.config.member(member).last_played()).strftime("%d %B %H:%M") if await self.config.member(member).last_played() != None else "No matches played yet.", inline=False)
        history = await self.config.member(member).get_raw("match_history")
        times = list(history.keys())
        times.sort()
        msg = ""
        for m in times[-20:]:
            res = "won" if history[m]["win"] else "lost"
            msg += f"[{datetime.fromtimestamp(int(m)).strftime('%d %B %H:%M')}] {res} vs {self.bot.get_user(history[m]['opponent']).mention} `{history[m]['elo_old']}` > `{history[m]['elo_new']}`\n"
        embed.add_field(name="Match History", value=msg if msg != "" else "No matches played yet.", inline=False)
        await ctx.send(embed=embed)
        
