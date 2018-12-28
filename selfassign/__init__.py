from .selfassign import SelfAssign


def setup(bot):
    bot.add_cog(SelfAssign(bot))
