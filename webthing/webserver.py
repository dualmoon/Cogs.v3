from aiohttp import web
import asyncio


class WebServer:

    def __init__(self):
        self.app = web.Application()
        self.port = 8088
        self.handler = None
        self.runner = None
        self.div = ""

    def __unload(self):
        self.bot.loop.create_task(self.runner.cleanup())

    async def make_webserver(self):
        async def root_get(request):
            # response logic goes here.
            return web.Response(text="<h1>this is a test</h1>", content_type='text/html')

        async def root_post(request):
            pass

        await asyncio.sleep(10)
        # router work goes here -- define pages
        self.app.router.add_get('/', root_get)
        self.app.router.add_post('/', root_post)

        # create our async runner
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        # configure handler
        self.handler = self.app.make_handler(debug=True)
        self.handler = web.TCPSite(self.runner, '0.0.0.0', self.port)
        await self.handler.start()
        print('WebTest started...')

    async def get_message(self, message):
        pass

    async def reloadhtml(self):
        pass
