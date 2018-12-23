from .webtest import WebTest
from redbot.core import commands


class WebThing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.web = WebTest(bot)
        self.bot.loop.create_task(self.web.make_webserver())
