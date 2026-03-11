from collections.abc import Callable
from typing import Any, Dict

from aioesphomeapi import (
    APIClient,
    APIConnectionError,
    EntityInfo,
    EntityState,
    ReconnectLogic,
)

from .models import NevermoreEspClientParams
from .nevermore_log_adapter import NevermoreLogAdapter


class NevermoreEspClient:
    watched_keys: Dict[int, str] = {}
    callbacks = {}
    connect_callbacks: list[Callable[[], None]] = []
    disconnect_callbacks: list[Callable[[], None]] = []

    _fan_speed_key: int = None
    _vent_percent_key: int = None

    def __init__(
        self, logger: NevermoreLogAdapter, client_params: NevermoreEspClientParams
    ):
        # Initialize variables
        self.client_params = client_params
        self.logger = logger
        self.cli = None
        self.reconnect_logic = None
        client_name = "Esphome nevermore controller"
        self.client_info = f"{client_name} 1.0.0.1"

    def set_fan_speed(self, speed: int):
        try:
            self.cli.number_command(self._fan_speed_key, speed)
        except Exception as e:
            self.logger.error("Failed to set fan speed", exc_info=e)

    def set_vent_percent(self, opening: int):
        try:
            self.cli.number_command(self._vent_percent_key, opening)
        except Exception as e:
            self.logger.error("Failed to set vent percent", exc_info=e)

    def on_fan_rpm_update(self, callback: Callable[[float], None]):
        self._on_event("fan_rpm", lambda object_id, value: callback(value))

    def on_fan_speed_update(self, callback: Callable[[int], None]):
        self._on_event("fan_speed", lambda object_id, value: callback(value))

    def on_temp_sensor_update(self, callback: Callable[[str, float], None]):
        self._on_event("intake_humidity", callback)
        self._on_event("exhaust_humidity", callback)
        self._on_event("intake_temperature", callback)
        self._on_event("exhaust_temperature", callback)
        self._on_event("intake_pressure", callback)
        self._on_event("exhaust_pressure", callback)
        self._on_event("intake_gas", callback)
        self._on_event("exhaust_gas", callback)

    def _on_event(self, event_name, callback):
        if event_name not in self.callbacks:
            self.callbacks[event_name] = [callback]
        else:
            self.callbacks[event_name].append(callback)

    def _emit_event(self, event_name, value: Any):
        if self.callbacks is not None and event_name in self.callbacks:
            for callback in self.callbacks[event_name]:
                callback(event_name, value)

    """Connect to an ESPHome device and wait for state changes."""

    def _change_callback(self, state: EntityState):
        """Print the state changes of the device..."""
        if state.key in self.watched_keys:
            event_name = self.watched_keys[state.key]
            self._emit_event(event_name, state.state)

    @staticmethod
    def _get_entity_key(entity_infos: list[EntityInfo], object_id: str) -> int | None:
        found = next((x for x in entity_infos if x.object_id == object_id), None)
        if found is None:
            return None
        return found.key

    def on_connect(self, callback: Callable[[], None]):
        self.connect_callbacks.append(callback)

    def on_disconnect(self, callback: Callable[[], None]):
        self.disconnect_callbacks.append(callback)

    async def _on_connect(self) -> None:
        self.logger.info("Connected to esp")
        try:
            self.watched_keys.clear()

            entity_infos, services = await self.cli.list_entities_services()

            # Get keys for sensors we want to listen to
            object_mapping = vars(self.client_params.object_ids)

            failed_to_find_an_object = False

            for object_name, object_id in object_mapping.items():
                entity = next(
                    (x for x in entity_infos if x.object_id == object_id), None
                )
                if entity is None:
                    self.logger.warning(
                        f"Unable to find object '{object_id}' for '{object_name}'"
                    )
                    failed_to_find_an_object = True
                else:
                    if object_name == object_id:
                        self.logger.debug(
                            f"Found object '{object_id}' with key {entity.key}"
                        )
                    else:
                        self.logger.debug(
                            f"Found object '{object_id}' for '{object_name}' with key {entity.key}"
                        )

                    if entity.key in self.watched_keys:
                        self.logger.error(
                            f"Object id '{object_id}' already used by '{self.watched_keys[entity.key]}' cannot bind it to '{object_name}'"
                        )
                    else:
                        self.watched_keys[entity.key] = object_name

            # Get key for fan speed
            self._fan_speed_key = self._get_entity_key(
                entity_infos, self.client_params.object_ids.fan_speed
            )

            self._vent_percent_key = self._get_entity_key(
                entity_infos, self.client_params.object_ids.vent_percent
            )

            if failed_to_find_an_object or self._fan_speed_key is None or self._vent_percent_key is None:
                self.logger.info('Failed to find a least one object, here is the full list of object ids :')
                for o in entity_infos:
                    self.logger.info(f'{o.object_id}')


            # Subscribe to the state changes
            self.cli.subscribe_states(self._change_callback)

            for callback in self.connect_callbacks:
                callback()

        except APIConnectionError as err:
            self.logger.error(
                f"Error getting initial data for {self.hostname}", exc_info=err
            )
            # Re-connection logic will trigger after this
            await self.cli.disconnect()
        except Exception as e:
            self.logger.error("Unhandled exception", exc_info=e)

    async def _on_disconnect(self, expected_disconnect) -> None:
        """Run disconnect stuff on API disconnect."""
        for callback in self.disconnect_callbacks:
            callback()

        if not expected_disconnect:
            self.logger.warning("Unexpected disconnect from esp")
        else:
            self.logger.info("Disconnected from esp")

    async def on_connect_error(self, err: Exception) -> None:
        """Show connection errors."""
        self.logger.error(f"Failed to connect with error '{err}'")

    async def start(self):
        self.cli = APIClient(
            self.client_params.hostname,
            6053,
            self.client_params.password,
            client_info=self.client_info,
            noise_psk=self.client_params.encryption_key,
            keepalive=self.client_params.keep_alive,
        )

        self.reconnect_logic = ReconnectLogic(
            client=self.cli,
            on_connect=self._on_connect,
            on_disconnect=self._on_disconnect,
            on_connect_error=self.on_connect_error,
        )

        await self.reconnect_logic.start()

    async def disconnect(self):
        self.logger.debug(f"Disconnecting client {self.hostname}")
        await self.reconnect_logic.stop()
        await self.cli.disconnect()
