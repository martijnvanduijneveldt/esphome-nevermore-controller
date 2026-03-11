from dataclasses import dataclass
from typing import Optional


@dataclass
class NevermoreEspClientObjectIdMapping(object):
    fan_rpm: str
    fan_speed: str
    intake_humidity: str
    intake_temperature: str
    intake_pressure: str
    intake_gas: str
    exhaust_humidity: str
    exhaust_temperature: str
    exhaust_pressure: str
    exhaust_gas: str
    vent_percent: str


@dataclass
class NevermoreEspClientParams:
    hostname: str
    password: Optional[str]
    encryption_key: Optional[str]
    keep_alive: float
    object_ids: NevermoreEspClientObjectIdMapping
