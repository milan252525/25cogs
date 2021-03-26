import discord
from redbot.core import commands
from discord_slash import SlashCommand
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import remove_all_commands

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

    @classmethod
    def from_interaction(cls, interaction, content: str):
        return cls(
            content,
            state=interaction._state,
            id=interaction.id,
            channel=interaction.channel,
            author=interaction.author,
        )

class Slash(commands.Cog):
    def __init__(self, bot):
        if not hasattr(bot, "slash"):
            bot.slash = SlashCommand(bot, sync_on_cog_reload=True)
        self.bot = bot

    def cog_unload(self):
        self.bot.slash.remove_cog_commands(self)

    @cog_ext.cog_slash(
        name="ptest", 
        description="Get your BS stats",
        guild_ids=[401883208511389716]
    )
    async def p_test(self, ctx: SlashContext, member = None):
        await ctx.respond()
        fake_message = FakeMessage(
            content= f"/profile {member}" if member is not None else "/profile",
            channel= ctx.channel,
            author=ctx.author,
            id=ctx.interaction_id,
            state=self.bot._connection
        )
        await self.bot.process_commands(fake_message)

        #msg = await ctx.send(content="Retrieving profile...", delete_after=0.01)
        #msg.content = f"/profile {member}" if member is not None else "/profile"
        #msg.author = ctx.author
        #await self.bot.process_commands(msg)

        