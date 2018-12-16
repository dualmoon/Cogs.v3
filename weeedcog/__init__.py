from .weeed import Weeedbot
from redbot.core import data_manager
from shutil import rmtree


def setup(bot):
    cog = Weeedbot(bot)
    rmtree(data_manager.cog_data_path(cog))
    data_manager.load_bundled_data(cog, __file__)
    bot.add_cog(cog)
