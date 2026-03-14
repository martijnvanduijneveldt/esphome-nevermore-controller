from configfile import ConfigWrapper


from .esphome_nevermore_library.nevermore import Nevermore

__all__ = [
    "load_config",
    "load_config_prefix"
]

def load_config(config: ConfigWrapper):
    return Nevermore(config)

# Allow custom names
def load_config_prefix(config: ConfigWrapper):
    return load_config(config)