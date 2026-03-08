import logging

from configfile import ConfigWrapper
from .nevermore_esp_client_thread import NevermoreEspClientThread
from .nevermore_log_adapter import NevermoreLogAdapter
from klippy import Printer

from .nevermore_fan import NevermoreFan



class Nevermore:
    def __init__(self, config: ConfigWrapper) -> None:
        self.name = config.get_name().split()[-1]
        self.printer: Printer = config.get_printer()

        self.hostname = config.get("host")

        self.logger = NevermoreLogAdapter(logging.getLogger(self.name), self.hostname)


        self.client_thread = NevermoreEspClientThread(self.logger, self.hostname)

        self.fan = NevermoreFan(self.printer, self.name, self.client_thread.client)

        self.logger.info("Initialized nevermore'")

        self.printer.add_object(f"Nevermore {self.name}", self)
        self.printer.register_event_handler("klippy:connect", self._handle_connect)
        self.printer.register_event_handler("klippy:shutdown", self._handle_shutdown)
        self.printer.register_event_handler(
            "gcode:request_restart", lambda t: self._handle_shutdown()
        )

    def _handle_connect(self):
        self.client_thread.start()


    def _handle_shutdown(self):
        self.client_thread.stop()

