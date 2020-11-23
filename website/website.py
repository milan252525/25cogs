import discord
from redbot.core import commands, Config, checks
import pymongo

class Website(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.db = pymongo.MongoClient("mongodb://localhost:27017/")["laclubs"]
       
    @commands.command()
    async def addclub(self, ctx, tag:str, name:str, region:str, country:str):
        if ctx.author.id not in (230947675837562880, 425260327425409028):
            return
        club = {
            "name": name,
            "tag": tag.upper().strip("#"),
            "region": region.upper(),
            "country": country.upper()
        }
        self.db['tracked_clubs'].update_one(
            {'tag': tag.upper().strip("#")},
            {'$set': club},
            upsert=True
        )

    @commands.command()
    async def delclub(self, ctx, tag:str):
        if ctx.author.id not in (230947675837562880, 425260327425409028):
            return
        self.db['tracked_clubs'].delete_one(
            {'tag': tag.upper().strip("#")}
        )
