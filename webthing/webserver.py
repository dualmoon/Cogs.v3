from aiohttp import web


class WebServer:
    def __init__(self, port: int = 8088, host: str = '0.0.0.0'):
        self.app = web.Application()
        self.port = port
        self.host = host
        self.handler = None
        self.runner = None

    def shutdown(self, loop):
        loop.create_task(self.runner.cleanup())

    async def make_webserver(self):
        async def root_get(request):
            # response logic goes here.
            return web.Response(text="<h1>this is a test</h1>", content_type='text/html')

        # router work goes here -- define pages
        self.app.router.add_get('/', root_get)

        # create our async runner
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        # configure handler
        self.handler = web.TCPSite(self.runner, self.host, self.port)
        await self.handler.start()
        print(f"Web server started at {self.host}:{self.port}...")
