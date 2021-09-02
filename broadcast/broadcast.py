import discord
from discord import colour
from redbot.core import commands, Config, checks

from typing import Union
import asyncio


class Broadcast(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=20925250209)
        default_global = {"broadcasts" : {}}
        self.config.register_global(**default_global)
        self.cached_conf = None

    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if self.cached_conf is None:
            self.cached_conf = await self.config.broadcasts()
        if message.author.bot and message.author != self.bot.user:
            return
        for bc, value in self.cached_conf.items():
            if message.channel.id in value["channels"]:
                embed=None
                if not message.author.bot or not message.embeds:
                    embed = discord.Embed(colour=message.author.colour)
                    name = f"{message.author.name} [{message.author.nick}]" if message.author.nick else f"{message.author.name}"
                    embed.set_author(name=name, icon_url=message.author.avatar_url, url=message.jump_url)
                    embed.set_footer(text=f"#{message.channel.name} | {message.guild.name}⠀")
                    embed.description = message.content[:1995] if message.content != "" else None
                    for role in message.role_mentions:
                        embed.description = embed.description.replace(f"<@&{role.id}>", "@"+role.name)
                    if message.attachments:
                        start = 0
                        if "image" in message.attachments[0].content_type:
                            embed.set_image(url=message.attachments[0].url)
                            start = 1
                        for i in range(start, len(message.attachments)):
                            embed.add_field(name=f"Attachment {str(i+1)}:", value=message.attachments[i].url, inline=False)
                    if message.stickers:
                        if not embed.image != discord.Embed.Empty:
                            embed.set_image(url=message.stickers[0].image_url)
                        else:
                            embed.add_field(name=f"Sticker", value=message.stickers[0].image_url, inline=False)
                elif message.author.bot and message.embeds:
                    if message.embeds[0].footer.text == discord.Embed.Empty or "⠀" not in message.embeds[0].footer.text:
                        embed=message.embeds[0]
                        if embed.footer.text != discord.Embed.Empty:
                            embed.set_footer(text=embed.footer.text+"⠀")
                        else: 
                            embed.set_footer(text="⠀")

                if embed is None:
                    return

                for channel_id in value["channels"]:
                    if channel_id != message.channel.id:
                        channel = self.bot.get_channel(channel_id)
                        if channel is not None:
                            await channel.send(embed=embed)
                              

    @commands.guild_only()
    @commands.is_owner()
    @commands.command()
    async def subscribe(self, ctx, broadcast_name:str, channel:discord.TextChannel=None):
        if channel is None:
            channel = ctx.channel
        conf = await self.config.broadcasts()
        if broadcast_name not in conf.keys():
            await self.config.broadcasts.set_raw(broadcast_name, value={"channels": []})
        channels = await self.config.broadcasts.get_raw(broadcast_name, "channels")
        if channel.id not in channels:
            channels.append(channel.id)
            await self.config.broadcasts.set_raw(broadcast_name, value={"channels": channels})
        else:
            return await ctx.send(f"Already subscribed to {broadcast_name}!")
        self.cached_conf = await self.config.broadcasts()
        await ctx.send(f"Subscribed to {broadcast_name}!")

    @commands.guild_only()
    @commands.is_owner()
    @commands.command()
    async def unsubscribe(self, ctx, broadcast_name:str, channel:discord.TextChannel=None):
        if channel is None:
            channel = ctx.channel
        conf = await self.config.broadcasts()
        if broadcast_name not in conf.keys():
            return await ctx.send(f"{broadcast_name} doesn't exist!")
        channels = await self.config.broadcasts.get_raw(broadcast_name, "channels")
        if channel.id not in channels:
            return await ctx.send(f"That channel wasn't subscribed to {broadcast_name}!")
        else:
            channels.remove(channel.id)
            await self.config.broadcasts.set_raw(broadcast_name, value={"channels": channels})
        self.cached_conf = await self.config.broadcasts()
        await ctx.send(f"Unsubscribed from {broadcast_name}!")

    @commands.guild_only()
    @commands.is_owner()
    @commands.command()
    async def broadcasts(self, ctx):
        conf = await self.config.broadcasts()
        msg = "**BROADCASTS:**\n"
        for bc in conf.keys():
            msg += f"**{bc}**:\n"
            for chan in conf[bc]['channels']:
                channel = self.bot.get_channel(chan)
                if channel is None:
                    msg += f"↳ None - {chan}\n"
                else:
                    msg += f"↳ {channel.mention} {channel.guild.name}\n"
        await ctx.send(msg[:2000])
