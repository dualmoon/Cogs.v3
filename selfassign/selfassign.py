from redbot.core import commands, Config, checks
from redbot.core.bot import Red
import discord


class SelfAssign(commands.Cog):
    """Allows users to self-assign roles from a designated list"""

    def __init__(self, red: Red):
        self.bot = red
        self.config = Config.get_conf(
            self, identifier=901101100011101010110111001100001)
        default_guild = {
            "VALID_ROLE_IDS": []
        }
        self.config.register_guild(**default_guild)

    @commands.group()
    async def selfassign(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            pass

    @selfassign.command(name="set")
    @checks.mod()
    async def sa_set(self, ctx, *, role: str):
        """Flags a given role as self-assignable"""
        valid_role = discord.utils.find(
            lambda m: m.name.lower() == role.lower(), ctx.guild.roles)
        if not valid_role:
            await ctx.send(f"Couldn't find a valid role called {role}")
        else:
            if ctx.author.top_role > valid_role:
                async with self.config.guild(ctx.guild).VALID_ROLE_IDS() as roles:
                    if valid_role.id in roles:
                        await ctx.send(f"The '{valid_role}' role is already self-assignable")
                        return
                    roles.append(valid_role.id)
                    await ctx.send(f"The '{valid_role}' role is now self-assignable")
            else:
                await ctx.send(f"You do not have permissions to make that role self-assignable.")

    @selfassign.command(name="unset")
    @checks.mod()
    async def sa_unset(self, ctx, *, role: str):
        """Removes a role from the allowed self-assign list. Role must be a string, NOT a snowflake (e.g. @Role)"""
        valid_role = discord.utils.find(
            lambda m: m.name.lower() == role.lower(), ctx.guild.roles)
        if not valid_role:
            await ctx.send(f"Couldn't find a valid role called '{role}'")
        else:
            async with self.config.guild(ctx.guild).VALID_ROLE_IDS() as roles:
                if valid_role.id not in roles:
                    await ctx.send(f"The '{valid_role}' role is not self-assignable")
                    return
                roles.remove(valid_role.id)
                await ctx.send(f"The '{valid_role}' role is no longer self-assignable")

    @selfassign.command(name="list")
    @checks.mod()
    async def sa_list(self, ctx):
        """Lists roles that can be self-assigned, sorted alphabetically"""
        roles_list = []
        async with self.config.guild(ctx.guild).VALID_ROLE_IDS() as roles:
            for i in roles:
                this_role = discord.utils.find(
                    lambda m: m.id == i, ctx.guild.roles)
                roles_list.append(this_role.name)
            roles_list.sort()
            await ctx.send(f"Current self-assignable roles: {roles_list}")

    @selfassign.command(name="give")
    async def sa_give(self, ctx, *, role: str):
        """Allows a user to have a role assigned to them by request. Role must be a string, NOT a snowflake (e.g. @Role)"""
        valid_role = discord.utils.find(
            lambda m: m.name.lower() == role.lower(), ctx.guild.roles)
        if not valid_role:
            await ctx.send(f"Couldn't find a valid role called '{role}'")
            return
        async with self.config.guild(ctx.guild).VALID_ROLE_IDS() as roles:
            if valid_role.id in roles:
                if valid_role in ctx.message.author.roles:
                    await ctx.send(f"You already have the '{valid_role}' role!")
                else:
                    await ctx.author.add_roles(valid_role)
                    await ctx.send(f"You now have the '{valid_role}' role!")
            else:
                await ctx.send(f"The '{valid_role}' role isn't set up for self assignment. If you think it should, please pings Mods!")

    @selfassign.command(name="take")
    async def sa_take(self, ctx, *, role: str):
        """Allows a user to have a role removed from them by request. Role must be a string, NOT a snowflake (e.g. @Role)"""
        valid_role = discord.utils.find(
            lambda m: m.name.lower() == role.lower(), ctx.guild.roles)
        if not valid_role:
            await ctx.send(f"Couldn't find a valid role called '{role}'")
            return
        async with self.config.guild(ctx.guild).VALID_ROLE_IDS() as roles:
            if valid_role.id in roles:
                if valid_role not in ctx.message.author.roles:
                    await ctx.send(f"You don't have the '{valid_role}' role!")
                else:
                    await ctx.author.remove_roles(valid_role)
                    await ctx.send(f"You no longer have the '{valid_role}' role!")
            else:
                await ctx.send(f"The '{valid_role}' role isn't set up for self assignment.")
