from abc import ABC, abstractmethod
from typing import Callable, Dict, Optional

from configfile import ConfigWrapper
from .constants import default_nevermore_name
from .nevermore import Nevermore


class NevermorePlotSensor(ABC):
    def __init__(self, config: ConfigWrapper) -> None:

        self.nevermore_name: str = config.get("nevermore_name", default_nevermore_name)
        self.sensor_kind = config.getchoice("sensor_kind", ["intake", "exhaust"])

        self.printer = config.get_printer()
        self.name = config.get_name().split()[-1]
        self.temp = self.min_temp = self.max_temp = 0.0
        self._callback: Optional[Callable[[float, float], None]] = None

        self.printer.add_object(f"temperature_sensor {self.name}", self)
        self.printer.register_event_handler("klippy:connect", self._handle_connect)

        self._timer_sample = self.printer.get_reactor().register_timer(self._sample)


    def _handle_connect(self) -> None:
        nevermore = self.printer.lookup_object(
            f"esphome_nevermore {self.nevermore_name}", None
        )
        if not isinstance(nevermore, Nevermore):
            raise self.printer.config_error(
                f"`Could not find a nevermore with name {self.nevermore_name}"
            )

        self.nevermore = nevermore
        self.bind_sensor_update()

        reactor = self.printer.get_reactor()
        reactor.update_timer(self._timer_sample, reactor.NOW)

    @abstractmethod
    def bind_sensor_update(self):
        pass


    def on_sensor_update(self, value: float):
        self.nevermore.logger.debug(f"Temp {self.sensor_kind} sensor update received  -> {value}")
        self.temp = round(value, 2)

    def get_status(self, event_time: float) -> Dict[str, float | None]:
        # Make of coppy to update data
        return {
            'temperature': self.temp
        }

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

    def _sample(self, eventtime: float) -> None:
        measured_time = self.printer.get_reactor().monotonic()

        if self.temp is not None and self._callback is not None:
            self._callback(measured_time, self.temp)

        return measured_time + self.get_report_time_delta()
