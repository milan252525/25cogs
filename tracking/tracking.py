import discord
from redbot.core import commands, Config, checks
from discord.ext import tasks
import brawlstats
from time import time

class Tracking(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.bsconfig = Config.get_conf(None, identifier=5245652, cog_name="BrawlStarsCog")
        self.config = Config.get_conf(self, identifier=25253332525)
        default_user = {"tracking_enabled" : False, "stored_stats" : {}, "reached_goals" : {}}
        self.config.register_user(**default_user)

    async def initialize(self):
        ofcbsapikey = await self.bot.db.api_tokens.get_raw("ofcbsapi", default={"api_key": None})
        if ofcbsapikey["api_key"] is None:
            raise ValueError("The Official Brawl Stars API key has not been set. Use [p]set api ofcbsapi api_key,YOURAPIKEY")
        self.ofcbsapi = brawlstats.OfficialAPI(ofcbsapikey["api_key"], is_async=True)

    def badEmbed(self, text):
        bembed = discord.Embed(color=0xff0000)
        bembed.set_author(name=text, icon_url="https://i.imgur.com/dgE1VCm.png")
        return bembed
        
    def goodEmbed(self, text):
        gembed = discord.Embed(color=0x45cafc)
        gembed.set_author(name=text, icon_url="https://i.imgur.com/fSAGoHh.png")
        return gembed

    async def update(self):
        users = await self.config.all_users()
        for uk in users.keys():
            if users[uk]["tracking_enabled"]:
                user = self.bot.get_user(uk)
                tag = await self.bsconfig.user(user).tag()
                try:
                    stats = await self.ofcbsapi.get_player(tag)
                except brawlstats.errors.RequestError:
                    continue

                await self.config.user(user).stored_stats.set_raw(int(time()), value=stats)


    @commands.guild_only()
    @commands.group(invoke_without_command=False)
    async def tracking(self, ctx):
        pass

    @commands.is_owner()
    @commands.has_permissions() 
    @tracking.command(name="update")
    async def tracking_update(self, ctx):
        await self.update()
        await ctx.send(embed = self.goodEmbed("Updated"))


    @commands.guild_only()
    @commands.has_permissions() 
    @tracking.command(name="enable")
    async def tracking_enable(self, ctx):
        tag = await self.bsconfig.user(ctx.author).tag()
        if tag is None:
            return await ctx.send(embed = self.badEmbed(f"You don't have a tag saved! Use {ctx.prefix}bssave <yourtag>"))
        try:
            player = await self.ofcbsapi.get_player(tag)
            
        except brawlstats.errors.NotFoundError:
            return await ctx.send(embed = self.badEmbed("No player with this tag found, try again!"))

        except brawlstats.errors.RequestError as e:
            return await ctx.send(embed = self.badEmbed(f"BS API is offline, please try again later! ({str(e)})"))

        if "LA" not in player.club.name:
            return await ctx.send(embed = self.badEmbed("Sorry, this feature is only available for LA members."))

        await self.config.user(ctx.author).tracking_enabled.set(True)
        await ctx.send(embed = self.goodEmbed("Your stats will now be tracked!"))