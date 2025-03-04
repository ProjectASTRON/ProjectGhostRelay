from __future__ import annotations

import asyncio

from aiohttp import web

from . import utils
from .log import logger


class HttpServer:
    def __init__(self, host: str, port: int, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._loop = loop or asyncio.get_event_loop()
        self._host = host
        self._port = port
        self._app = web.Application(loop=self._loop)
        self._main_atask: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    @property
    def app(self) -> web.Application:
        return self._app

    @property
    def port(self) -> int:
        return self._port

    async def start(self) -> None:
        async with self._lock:
            handler = self._app.make_handler()
            self._server = await self._loop.create_server(handler, self._host, self._port)

            if self._port == 0:
                self._port = self._server.sockets[0].getsockname()[1]

            self._main_atask = asyncio.create_task(self._main_task(), name="HttpServer._main_task")

    @utils.log_exceptions(logger=logger)
    async def _main_task(self) -> None:
        await self._server.serve_forever()

    async def aclose(self) -> None:
        async with self._lock:
            self._server.close()
            await self._server.wait_closed()

            if self._main_atask:
                await self._main_atask
