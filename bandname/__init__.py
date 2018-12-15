from .bandname import BandName


def setup(bot):
    cog = BandName(bot)
    bot.add_cog(cog)
