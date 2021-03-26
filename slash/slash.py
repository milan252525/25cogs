import discord
from redbot.core import commands
from discord_slash import SlashCommand, cog_ext, SlashContext
from discord_slash.utils.manage_commands import remove_all_commands, create_option
from discord_slash.model import SlashCommandOptionType

from bs import get_stats

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
        if not hasattr(bot, "slash"):
            bot.slash = SlashCommand(bot, sync_on_cog_reload=True)
        self.bot = bot

    def cog_unload(self):
        self.bot.slash.remove_cog_commands(self)

    @cog_ext.cog_slash(
        name="profile", 
        description="Get your BS stats",
        options=[
            create_option(
                name="target",
                description="Discord user or BS tag",
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

        embed = await get_stats.get_profile_embed(self.bot, context, user)
        await ctx.send(embed=embed)

        