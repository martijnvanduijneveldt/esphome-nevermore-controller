from typing import Callable, Dict, Optional

from klippy import Printer

from .nevermore_esp_client import NevermoreEspClient
from .nevermore_log_adapter import NevermoreLogAdapter


class NevermoreSensor:
    def __init__(self, logger: NevermoreLogAdapter, printer: Printer, name:str, client:NevermoreEspClient) -> None:
        self.logger = logger
        self.printer = printer
        self.name = name
        self.client = client

        self.state = {}


        self.min_temp = self.max_temp = 0.0

        self._callback: Optional[Callable[[float, float], None]] = None

        self.client.on_temp_sensor_update(self.on_sensor_update)
        self.client.on_disconnect(self.on_disconnect)

        self.printer.add_object(f"nevermore {self.name}", self)

    def on_disconnect(self):
        # Reset states on disconnect
        self.state = {}

    def on_sensor_update(self, object_id,  value:float):
        self.state[object_id] = value

    def get_status(self, event_time: float) -> Dict[str, float|None]:
        # Make of coppy to update data
        return self.state.copy()

    # required by sensors API
    def setup_minmax(self, min_temp: float, max_temp: float) -> None:
        self.min_temp = min_temp
        self.max_temp = max_temp

    # required by sensors API
    def setup_callback(self, cb: Callable[[float, float], None]) -> None:
        self._callback = cb

    # required by sensors API
    def get_report_time_delta(self) -> float:
        return 2
