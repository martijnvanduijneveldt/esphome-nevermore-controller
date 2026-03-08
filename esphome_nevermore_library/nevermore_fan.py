from typing import Dict

from gcode import GCodeCommand, GCodeDispatch
from klippy import Printer

from .nevermore_esp_client import NevermoreEspClient


class NevermoreFan:
    cmd_SET_FAN_SPEED_help = "Sets the speed of a nevermore fan"

    def __init__(self, printer: Printer, name: str, client: NevermoreEspClient) -> None:
        self.printer = printer
        self.client = client
        self.name = f"{name}_fan"

        # Init fan state
        self.rpm = 0
        self.speed = 0

        gcode: GCodeDispatch = self.printer.lookup_object("gcode")
        gcode.register_mux_command(
            "SET_FAN_SPEED",
            "FAN",
            self.name,
            self.cmd_SET_FAN_SPEED,
            desc=self.cmd_SET_FAN_SPEED_help,
        )

        self.client.on_fan_speed_update(self._on_fan_speed_update)
        self.client.on_fan_rpm_update(self._on_fan_rpm_update)

        # Register fan on printer
        self.printer.add_object(f"fan_generic {self.name}", self)

    def _on_fan_speed_update(self, speed: float):
        self.speed = speed / 100

    def _on_fan_rpm_update(self, rpm: float):
        self.rpm = rpm

    def get_status(self, eventtime: float) -> Dict[str, float]:
        return {
            "speed": self.speed,
            "rpm": self.rpm,
        }

    def cmd_SET_FAN_SPEED(self, gcmd: GCodeCommand) -> None:
        speed: float = gcmd.get_float("SPEED")
        self.client.set_fan_speed(int(speed * 100))
