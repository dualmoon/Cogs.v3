from .selfassign import SelfAssign


async def setup(bot):
    await bot.add_cog(SelfAssign(bot))
