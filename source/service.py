#!/usr/bin/env python3

from pathlib import Path

from aiohttp import web


class Service:

    def __init__(self, port=8080):
        self.port = port
        self.static_folder = Path("./static")

        # init
        self.app = web.Application()
        self.app.router.add_get("/health", self.h_health)
        self.app.router.add_get("/", self.h_main)
        self.app.router.add_post("/api/process", self.h_api_process)

        self.app.router.add_static(
            "/static", self.static_folder, show_index=False)
    
    def run(self):
        web.run_app(self.app)
    
    async def h_main(self, request):
        return web.Response()
    
    async def h_api_process(self, request):
        """Infer image"""
        return web.Response()
    
    async def h_health(self, request):
        return web.Response(text="OK")


if __name__ == "__main__":
    srv = Service()
    srv.run()
