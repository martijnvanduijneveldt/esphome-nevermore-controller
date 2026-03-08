import asyncio
import threading
from .nevermore_esp_client import NevermoreEspClient
from .nevermore_log_adapter import NevermoreLogAdapter

class NevermoreEspClientThread:
    def __init__(self, logger: NevermoreLogAdapter, hostname: str):
        self.logger = logger
        self.hostname = hostname
        self.thread = threading.Thread(target=self._init_thread, args=(), daemon=True)
        self._disconnect = asyncio.Event()
        self.client = NevermoreEspClient(self.logger, self.hostname)

    def start(self):
        self.logger.debug("Background thread started")
        self.thread.start()

    def stop(self):
        self.logger.debug("Background thread stop received")
        self._disconnect.set()
        self.thread.join()

    async def start_client(self):
        await self.client.start()

    async def thread_loop(self, loop):
        loop.create_task(self.start_client())
        await self._disconnect.wait()
        await self.client.disconnect()

    def _init_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.thread_loop(loop))
