from .bandname import BandName


async def setup(bot):
    cog = BandName(bot)
    await bot.add_cog(cog)
