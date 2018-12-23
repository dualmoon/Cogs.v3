from .webserver import WebServer
from redbot.core import commands


class WebThing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.web = WebServer()
        self.bot.loop.create_task(self.web.make_webserver())

    def __unload(self):
        self.web.shutdown(self.bot.loop)
