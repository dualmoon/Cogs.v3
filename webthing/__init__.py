from .webthing import WebThing

def setup(bot):
    cog = WebThing(bot)
    bot.add_cog(cog)
