from .weeed import WeeedBot
from redbot.core import data_manager
from shutil import rmtree


def setup(bot):
    cog = WeeedBot(bot)
    bot.add_cog(cog)
