import logging
from typing import Optional

from configfile import ConfigWrapper
from gcode import GCodeCommand, GCodeDispatch
from klippy import Printer

from .models import (
    NevermoreEspClientObjectIdMapping,
    NevermoreEspClientParams,
)
from .nevermore_chip import NevermoreChip
from .nevermore_esp_client import NevermoreEspClient
from .nevermore_esp_client_thread import NevermoreEspClientThread
from .nevermore_fan import NevermoreFan
from .nevermore_log_adapter import NevermoreLogAdapter
from .nevermore_sensor import NevermoreSensor


class Nevermore:
    def __init__(
        self, config: ConfigWrapper, esp_client_thread: NevermoreEspClientThread
    ) -> None:
        self.name = config.get_name().split()[-1]
        self.printer: Printer = config.get_printer()

        self.hostname = config.get("host")

        self.logger = NevermoreLogAdapter(logging.getLogger(self.name), self.hostname)

        enable_debug_logs = config.getboolean("enable_debug_logs", False)
        if enable_debug_logs:
            self.logger.setLevel(level=logging.DEBUG)
            self.logger.debug("Debug logs enabled")

        params = NevermoreEspClientParams(
            hostname=self.hostname,
            password=config.get("password", None),
            port=config.getint("port", 6053),
            encryption_key=config.get("encryption_key", None),
            keep_alive=config.getfloat("esp_keepalive", 2.0, 0.1, 30),
            object_ids=NevermoreEspClientObjectIdMapping(
                fan_rpm=config.get("override_id_fan_rpm", "fan_rpm"),
                fan_speed=config.get("override_id_fan_speed", "fan_speed"),
                intake_humidity=config.get(
                    "override_id_intake_humidity", "intake_humidity"
                ),
                intake_temperature=config.get(
                    "override_id_intake_temperature", "intake_temperature"
                ),
                intake_pressure=config.get(
                    "override_id_intake_pressure", "intake_pressure"
                ),
                intake_gas=config.get("override_id_intake_voc", "intake_voc"),
                exhaust_humidity=config.get(
                    "override_id_exhaust_humidity", "exhaust_humidity"
                ),
                exhaust_temperature=config.get(
                    "override_id_exhaust_temperature", "exhaust_temperature"
                ),
                exhaust_pressure=config.get(
                    "override_id_exhaust_pressure", "exhaust_pressure"
                ),
                exhaust_gas=config.get("override_id_exhaust_voc", "exhaust_voc"),
                vent_percent=config.get("override_id_vent_percent", "vent_percent"),
            ),
        )

        self.client = NevermoreEspClient(self.logger, params)

        esp_client_thread.add_client(self.client)

        self.nevermore_sensor = NevermoreSensor(
            self.logger, self.printer, self.name, self.client
        )

        self.nevermore_chip = NevermoreChip(
            self.logger, self.printer, self.name, self.client
        )
        self.fan = NevermoreFan(self.printer, self.name, self.client)

        gcode: GCodeDispatch = self.printer.lookup_object("gcode")
        gcode.register_mux_command(
            "ESPHOME_NEVERMORE_PRESS_BUTTON",
            "NEVERMORE",
            self.name,
            self.cmd_ESPHOME_NEVERMORE_PRESS_BUTTON,
            desc="Simulate a button press on esphome",
        )

        self.logger.info("Initialized nevermore")

        self.printer.add_object(f"esphome_nevermore {self.name}", self)

    def cmd_ESPHOME_NEVERMORE_PRESS_BUTTON(self, gcmd: GCodeCommand) -> None:
        button_id = gcmd.get("BUTTON_ID", None)
        if button_id is None:
            raise gcmd.error("Error on 'ESPHOME_NEVERMORE_PRESS_BUTTON': missing BUTTON_ID")

        success = self.client.press_button(button_id)
        if not success:
            raise gcmd.error(f"Failed to press button {button_id}, check logs")