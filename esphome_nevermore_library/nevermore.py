import logging

from configfile import ConfigWrapper
from klippy import Printer

from .models import (
    NevermoreEspClientObjectIdMapping,
    NevermoreEspClientParams,
)
from .nevermore_esp_client_thread import NevermoreEspClientThread
from .nevermore_fan import NevermoreFan
from .nevermore_log_adapter import NevermoreLogAdapter
from .nevermore_sensor import NevermoreSensor


class Nevermore:
    def __init__(self, config: ConfigWrapper) -> None:
        self.name = config.get_name().split()[-1]
        self.printer: Printer = config.get_printer()

        self.hostname = config.get("host")



        self.logger = NevermoreLogAdapter(logging.getLogger(self.name), self.hostname)

        params = NevermoreEspClientParams(
            hostname=self.hostname,
            password= config.get('password', None),
            encryption_key= config.get('encryption_key', None),
            keep_alive=config.getfloat("esp_keepalive", 2.0, 0.1, 30),
            object_ids= NevermoreEspClientObjectIdMapping(
                fan_rpm=config.get('override_id_fan_rpm', 'fan_rpm'),
                fan_speed = config.get('override_id_fan_speed', 'fan_speed'),
                intake_humidity = config.get('override_id_intake_humidity', 'intake_humidity'),
                intake_temperature = config.get('override_id_intake_temperature', 'intake_temperature'),
                intake_pressure = config.get('override_id_intake_pressure', 'intake_pressure'),
                intake_gas = config.get('override_id_intake_voc', 'intake_voc'),
                exhaust_humidity = config.get('override_id_exhaust_humidity', 'exhaust_humidity'),
                exhaust_temperature = config.get('override_id_exhaust_temperature', 'exhaust_temperature'),
                exhaust_pressure = config.get('override_id_exhaust_pressure', 'exhaust_pressure'),
                exhaust_gas = config.get('override_id_exhaust_voc', 'exhaust_voc'),
            )
        )

        self.client_thread = NevermoreEspClientThread(self.logger, params)

        self.fan = NevermoreFan(self.printer, self.name, self.client_thread.client)
        self.nevermore_sensor = NevermoreSensor(self.logger, self.printer, self.name, self.client_thread.client)

        self.logger.info("Initialized nevermore")

        self.printer.register_event_handler("klippy:connect", self._handle_connect)
        self.printer.register_event_handler("klippy:shutdown", self._handle_shutdown)
        self.printer.register_event_handler(
            "gcode:request_restart", lambda t: self._handle_shutdown()
        )

    def _handle_connect(self):
        self.client_thread.start()

    def _handle_shutdown(self):
        self.client_thread.stop()

