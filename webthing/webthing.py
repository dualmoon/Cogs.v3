from .webtest import WebTest
from redbot.core import checks, Config, commands
import discord
import asyncio
from aiohttp import web

class WebThing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.web = WebTest(bot)
        self.bot.loop.create_task(self.web.make_webserver())

    async def on_message(self, message):
        await self.web.get_message(message)