import asyncio
import threading
from logging import Logger
from typing import List

from klippy import Printer

from .nevermore_esp_client import NevermoreEspClient


class NevermoreEspClientThread:
    def __init__(self, global_logger: Logger, printer: Printer):
        self._global_logger = global_logger
        self.thread = threading.Thread(target=self._init_thread, args=(), daemon=True)
        self._disconnect = asyncio.Event()
        self._clients: List[NevermoreEspClient] = []

        printer.register_event_handler("klippy:connect", self._handle_connect)
        printer.register_event_handler("klippy:shutdown", self._handle_shutdown)
        printer.register_event_handler(
            "gcode:request_restart", lambda t: self._handle_shutdown()
        )

    def _handle_connect(self):
        self._start()

    def _handle_shutdown(self):
        self._stop()

    def add_client(self, client: NevermoreEspClient):
        self._clients.append(client)

    def _start(self):
        self._global_logger.debug("Background thread started")
        self.thread.start()

    def _stop(self):
        self._global_logger.debug("Background thread stop received")
        self._disconnect.set()
        self.thread.join()

    async def start_clients(self):
        for client in self._clients:
            await client.start()

    async def thread_loop(self, loop):
        loop.create_task(self.start_clients())
        await self._disconnect.wait()
        await self.client.disconnect()

    def _init_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.thread_loop(loop))
