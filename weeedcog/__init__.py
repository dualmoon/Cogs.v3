from .weeed import WeeedBot
from redbot.core import data_manager
from shutil import rmtree


async def setup(bot):
    cog = WeeedBot(bot)
    await bot.add_cog(cog)
