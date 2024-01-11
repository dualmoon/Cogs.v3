from .webthing import WebThing

async def setup(bot):
    cog = WebThing(bot)
    await bot.add_cog(cog)
