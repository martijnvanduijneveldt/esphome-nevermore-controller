from configfile import ConfigWrapper
from klippy import Printer
import logging

from .esphome_nevermore_library.nevermore import Nevermore
from .esphome_nevermore_library.nevermore_esp_client_thread import NevermoreEspClientThread

__all__ = [
    "load_config",
    "load_config_prefix"
]

global_logger = logging.getLogger("esphome-nevermore-controller")

# We only want one background thread
def _get_or_create_client_thread(printer: Printer) -> NevermoreEspClientThread:
    obj = printer.lookup_object("NevermoreEspClientThread", default=None)
    if obj is not None:
        assert isinstance(obj, NevermoreEspClientThread)
        return obj

    obj = NevermoreEspClientThread(global_logger, printer)
    printer.add_object("NevermoreEspClientThread", obj)
    return obj

def load_config(config: ConfigWrapper):
    client_thread = _get_or_create_client_thread(config.get_printer())
    return Nevermore(config, client_thread)

# Allow custom names
def load_config_prefix(config: ConfigWrapper):
    return load_config(config)