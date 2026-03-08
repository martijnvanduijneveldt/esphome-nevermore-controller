from configfile import ConfigWrapper


from .esphome_nevermore_library.nevermore import Nevermore

__all__ = [
    "load_config",
]

def load_config(config: ConfigWrapper):
    return Nevermore(config)
