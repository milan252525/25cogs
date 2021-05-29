import discord
from redbot.core import commands
from discord_slash import SlashCommand, cog_ext, SlashContext
from discord_slash.utils.manage_commands import remove_all_commands, create_option
from discord_slash.model import SlashCommandOptionType
from redbot.core.utils.menus import menu, prev_page, next_page
from discord_components import DiscordComponents, Button, ButtonStyle, InteractionType

from bs import player_stats, game_stats

from typing import Union

#source - https://github.com/phenom4n4n/phen-cogs/blob/d8cb2bd78fa1edc1b7f85ce4b67add8c8fd7db9e/slashtags/objects.py#L349
def implement_partial_methods(cls):
    msg = discord.Message
    for name in discord.Message.__slots__:
        func = getattr(msg, name)
        setattr(cls, name, func)
    return cls

@implement_partial_methods
class FakeMessage(discord.Message):
    REIMPLEMENTS = {
        "reactions": [],
        "mentions": [],
        "attachments": [],
        "stickers": [],
        "embeds": [],
        "flags": discord.MessageFlags._from_value(0),
    }

    def __init__(
        self,
        content: str,
        *,
        channel: discord.TextChannel,
        author: discord.Member,
        id: int,
        state,
    ):
        self._state = state
        self.id = id
        self.channel = channel
        self.guild = channel.guild

        self.content = content
        self.author = author

        for name, value in self.REIMPLEMENTS.items():
            if not hasattr(self, name):
                setattr(self, name, value)

        for item in self.__slots__:
            if not hasattr(self, item):
                setattr(self, item, None)

class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        DiscordComponents(self.bot)

    def cog_unload(self):
        self.bot.slash.remove_cog_commands(self)

    @cog_ext.cog_slash(
        name="profile", 
        description="BS player stats",
        options=[
            create_option(
                name="target",
                description="Discord user, ID or BS tag",
                option_type=SlashCommandOptionType.STRING,
                required=False
            )
        ]
    )
    async def bs_profile(self, ctx: SlashContext, target:str=None):
        await ctx.defer()

        fake_message = FakeMessage(
            content= "...",
            channel= ctx.channel,
            author=ctx.author,
            id=int(ctx.interaction_id),
            state=self.bot._connection
        )
        context = await self.bot.get_context(fake_message)

        user = None
        if target is None:
            user = ctx.author
        else:
            try:
                member_converter = commands.MemberConverter()
                user = await member_converter.convert(context, target)
            except commands.MemberNotFound:
                user = target

        embed = await player_stats.get_profile_embed(self.bot, context, user)
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="brawlers", 
        description="BS player's brawler stats",
        options=[
            create_option(
                name="target",
                description="Discord user, ID or BS tag",
                option_type=SlashCommandOptionType.STRING,
                required=False
            )
        ]
    )
    async def bs_brawlers(self, ctx: SlashContext, target:str=None):
        await ctx.defer()

        fake_message = FakeMessage(
            content= "...",
            channel= ctx.channel,
            author=ctx.author,
            id=int(ctx.interaction_id),
            state=self.bot._connection
        )
        context = await self.bot.get_context(fake_message)

        user = None
        if target is None:
            user = ctx.author
        else:
            try:
                member_converter = commands.MemberConverter()
                user = await member_converter.convert(context, target)
            except commands.MemberNotFound:
                user = target

        embeds = await player_stats.get_brawlers_embeds(self.bot, context, user)
        ctx.me = context.guild.get_member(self.bot.user.id)
        ctx.bot = self.bot
        await menu(ctx=ctx, pages=embeds, controls={"⬅": prev_page, "➡": next_page}, timeout=300)

    @cog_ext.cog_slash(
        name="brawler", 
        description="BS player's detailed brawler stats",
        options=[
            create_option(
                name="brawler",
                description="Brawler name",
                option_type=SlashCommandOptionType.STRING,
                required=True
            ),
            create_option(
                name="target",
                description="Discord user, ID or BS tag",
                option_type=SlashCommandOptionType.STRING,
                required=False
            )
        ]
    )
    async def bs_brawler(self, ctx: SlashContext, brawler:str, target:str=None):
        await ctx.defer()

        fake_message = FakeMessage(
            content= "...",
            channel= ctx.channel,
            author=ctx.author,
            id=int(ctx.interaction_id),
            state=self.bot._connection
        )
        context = await self.bot.get_context(fake_message)

        user = None
        if target is None:
            user = ctx.author
        else:
            try:
                member_converter = commands.MemberConverter()
                user = await member_converter.convert(context, target)
            except commands.MemberNotFound:
                user = target

        embed = await player_stats.get_single_brawler_embed(self.bot, context, user, brawler)
        await ctx.send(embed=embed)

    @cog_ext.cog_slash( 
        name="events", 
        description="BS active and upcoming events",
    )
    async def bs_events(self, ctx: SlashContext):
        await ctx.defer()
        embeds = await game_stats.get_event_embeds(self.bot)
        await ctx.send(embeds=embeds)

    @cog_ext.cog_slash( 
        name="map", 
        description="BS map info",
        options=[
            create_option(
                name="name",
                description="Name of a map",
                option_type=SlashCommandOptionType.STRING,
                required=True
            )
        ]
    )
    async def bs_map(self, ctx: SlashContext, name:str):
        await ctx.defer()
        embed = await game_stats.get_map_embed(self.bot, name)
        await ctx.send(embed=embed)

    @cog_ext.cog_slash( 
        name="website", 
        description="LA BS website"
    )
    async def website(self, ctx: SlashContext):
        comp = [
            Button(style=ButtonStyle.URL, label="LA Clubs", url="https://laclubs.net/"),
        ]
        await ctx.send("Buttons:", components=comp)
