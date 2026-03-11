from typing import Dict, Optional


from gcode import GCodeCommand, GCodeDispatch
from klippy import Printer
from mcu import MCU

from .nevermore_log_adapter import NevermoreLogAdapter
from .nevermore_esp_client import NevermoreEspClient


class NevermoreVentServoPin:
    def __init__(self, logger: NevermoreLogAdapter, mcu: MCU, client:NevermoreEspClient):
        self.logger = logger
        self._real_mcu = mcu
        self.client = client

    def get_mcu(self):
        return self._real_mcu

    def setup_max_duration(self, max_duration):
        pass

    def setup_cycle_time(self, cycle_time, hardware_pwm=False):
        pass

    def setup_start_value(self, start_value, shutdown_value):
        pass

    def get_status(self, eventtime):
        return {
            'value': self._value,
            'type': 'pwm'
        }

    def set_pwm(self, print_time, value):
        self.logger.debug(f"Set vent : {value}")
        self.client.set_vent_servo(value)

class NevermoreChip:
    def __init__(self, logger:NevermoreLogAdapter, printer:Printer, name:str, client:NevermoreEspClient):
        self.logger = logger
        self._ppins = printer.lookup_object("pins")
        self._ppins.register_chip(f"{name}", self)

        self._real_mcu: MCU = printer.lookup_object("mcu")
        self.logger.info(self._real_mcu)
        self._client = client

    def setup_pin(self, pin_type, pin_params):
        # Validate pin config
        name = pin_params['pin']

        self.logger.info(pin_type)
        self.logger.info(pin_params)

        if name != 'vent_servo':
            raise self._ppins.error("nevermore only support `vent_servo` pin")

        if pin_type != 'pwm':
            raise self._ppins.error("nevermore servo should have `pwm: True`")

        return NevermoreVentServoPin(self.logger, self._real_mcu, self._client)