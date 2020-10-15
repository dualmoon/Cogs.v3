import re
from random import choice, random
from typing import Union

import discord
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.commands import Context


class BandName(commands.Cog):
    """ Fun cog that randomly turns user messages into band names. """

    def __init__(self, red: Red):
        print('Initializing BandName..........')
        self.bot = red
        configID = 901101100011101010110111001100001
        self.config = Config.get_conf(self, identifier=configID)
        self.default_config = {
            "genres": ["emo", "metal", "country", "pop", "punk"]
        }
        self.default_config_guild = {
            # list of channel IDs to blacklist
            "channel_blacklist": [],
            # boolean of whether or not the server has the cog blacklisted
            "disabled": False,
            # int of probability modifier
            "p_mod": 0,
            # int of probability scaling
            "p_scale": 0.5,
        }
        self.config.register_global(**self.default_config)
        self.config.register_guild(**self.default_config_guild)
        self.blacklists = ["http", "www", "@", '#']
        self.blacklist_regex = re.compile(r"^(.\!\w|[^\w])")

    async def on_message(self, message):
        print('bandname bot triggered.')
        if message.author == self.bot.user:
            return
        if type(message.channel) != discord.TextChannel:
            return
        # TODO: reorder these so that the most common disqualifiers are checked first
        # check for channel or server blacklisted, etc
        guild_config = self.config.guild(message.guild)
        # check if the guild has this cog disabled completely
        guild_disabled = await guild_config.disabled()
        if guild_disabled:
            return
        # check if the guild has the channel the message came from blacklisted
        channel_blacklist = await guild_config.channel_blacklist()
        if message.channel.id in channel_blacklist:
            return
        # roughshod list that should exclude urls, mentions, channels
        if any(x in self.blacklists for x in message.content) or self.blacklist_regex.match(message.content):
            return
        # make sure the message is of the appropriate length
        if 1 < len(message.content.split()) < 5:
            # actually do the deal
            p_mod = await guild_config.p_mod()
            roll = random()*1000
            if roll+p_mod > 999:
                # pick a random genre
                genres = await self.config.genres()
                genre = choice(genres)
                # send the message
                band = message.content.strip()
                await message.channel.send(f"\"{band}\" is the name of my new {genre} band")
                await guild_config.p_mod.set(0)
            else:
                p_scale = await guild_config.p_scale()
                await guild_config.p_mod.set(p_mod+p_scale)


    @commands.group()
    async def bandname(self, ctx: Context):
        """Fun cog that randomly turns user messages into band names."""
        pass

    @bandname.group(name='set')
    @checks.mod()
    async def bandname_set(self, ctx: Context):
        """Changes settings for the bandname cog."""
        pass

    @bandname_set.command('pmod')
    async def bandname_set_pmod(self, ctx: Context, new_pmod: float = None):
        """View and set your probability modifier."""
        pmod = await self.config.guild(ctx.guild).p_mod()
        if not new_pmod:
            await ctx.send(f"P_mod for {ctx.guild.name} is {pmod}")
        else:
            if pmod == new_pmod:
                await ctx.send(f"P_mod for {ctx.guild.name} is already {pmod}")
            else:
                await self.config.guild(ctx.guild).p_mod.set(new_pmod)
                pmod = await self.config.guild(ctx.guild).p_mod()
                await ctx.send(f"P_mod for {ctx.guild.name} is now {pmod}")
    
    @bandname_set.command('pscale')
    async def bandname_set_pscale(self, ctx: Context, new_pscale: float = None):
        """View and set your probability scaling. Higher numbers mean more band names."""
        pscale = await self.config.guild(ctx.guild).p_scale()
        if not new_pscale:
            await ctx.send(f"P_scale for {ctx.guild.name} is {pscale}")
        else:
            if pscale == new_pscale:
                await ctx.send(f"P_scale for {ctx.guild.name} is already {pscale}")
            else:
                await self.config.guild(ctx.guild).p_scale.set(new_pscale)
                pscale = await self.config.guild(ctx.guild).p_scale()
                await ctx.send(f"P_scale for {ctx.guild.name} is now {pscale}")

    @bandname_set.command('toggle')
    async def bandname_set_toggle(self, ctx: Context):
        """Toggles the bandname cog on/off for this guild"""
        disabled = await self.config.guild(ctx.guild).disabled()
        await self.config.guild(ctx.guild).disabled.set(not disabled)
        disabled = await self.config.guild(ctx.guild).disabled()
        if disabled:
            status = "disabled"
        else:
            status = "enabled"
        await ctx.send(f"This cog is now {status} for {ctx.guild.name}")

    @bandname_set.command('genres')
    async def bandname_set_genres(self, ctx: Context, command: str=None, *, genre: str=None):
        """Allows you to add, remove, and view band genres."""
        genres = await self.config.genres()
        if not command:
            # Help, basically
            await ctx.send("Valid commands are 'add', 'del', and 'list'")
        else:
            if command == "list":
                await ctx.send(f"Current genre list: {repr(genres)}")
            elif not genre or genre.lower() != genre:
                await ctx.send(f"Please make the genre name all lower case.")
            else:
                if command == "add":
                    if genre in genres:
                        await ctx.send(f"{genre} is already present in the genre list!")
                    else:
                        genres.append(genre)
                        await self.config.genres.set(genres)
                        genres = await self.config.genres()
                        await ctx.send(f"New genre list: {repr(genres)}")
                elif command == "del":
                    if genre in genres:
                        genres.remove(genre)
                        await self.config.genres.set(genres)
                        genres = await self.config.genres()
                        await ctx.send(f"New genre list: {repr(genres)}")
                    else:
                        await ctx.send(f"{genre} was not found in the genre list!")

    @bandname_set.command('blacklist')
    async def bandname_set_blacklist(self, ctx: Context, command: str=None, *, channel: discord.TextChannel=None):
        """Allows you to blacklist channels for this cog."""
        channel_blacklist = await self.config.guild(ctx.guild).channel_blacklist()
        if not command:
            await ctx.send("Valid commands are 'add', 'del', and 'list'")
        else:
            if command == "add":
                if channel.id in channel_blacklist:
                    await ctx.send(f"#{channel.name} is already blacklisted.")
                else:
                    channel_blacklist.append(channel.id)
                    await self.config.guild(ctx.guild).channel_blacklist.set(channel_blacklist)
                    channel_blacklist = await self.config.guild(ctx.guild).channel_blacklist()
                    await ctx.send(f"New channel blacklist: {repr(channel_blacklist)}")
            elif command == "del":
                if channel.id in channel_blacklist:
                    channel_blacklist.remove(channel.id)
                    await self.config.guild(ctx.guild).channel_blacklist.set(channel_blacklist)
                    channel_blacklist = await self.config.guild(ctx.guild).channel_blacklist()
                    await ctx.send(f"New channel blacklist: {repr(channel_blacklist)}")
                else:
                    await ctx.send(f"{channel.name} was not found in the blacklist!")
            elif command == "list":
                await ctx.send(f"Current blacklist for {ctx.guild.name}: {repr([ctx.guild.get_channel(x) for x in channel_blacklist])}")
