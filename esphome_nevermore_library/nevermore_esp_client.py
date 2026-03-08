from .nevermore_log_adapter import NevermoreLogAdapter
from collections.abc import Callable
from typing import Dict, Any

from aioesphomeapi import (
    APIClient,
    APIConnectionError,
    ReconnectLogic,
    EntityState,
)


class NevermoreEspClient:
    watched_keys: Dict[int, str] = {}
    callbacks = {}

    _object_ids_to_find = ["fan_rpm", "fan_speed"]

    _fan_speed_key: int = None

    def set_fan_speed(self, speed: int):
        try:
            self.cli.number_command(self._fan_speed_key, speed)
        except Exception as e:
            self.logger.error("Failed to set fan speed", exc_info=e)

    def on_fan_rpm_update(self, callback: Callable[[float], None]):
        self._on_event("fan_rpm", callback)

    def on_fan_speed_update(self, callback: Callable[[int], None]):
        self._on_event("fan_speed", callback)

    def _on_event(self, event_name, callback):
        if self.callbacks is None:
            self.callbacks = {}

        if event_name not in self.callbacks:
            self.callbacks[event_name] = [callback]
        else:
            self.callbacks[event_name].append(callback)

    def _emit_event(self, event_name, value: Any):
        if self.callbacks is not None and event_name in self.callbacks:
            for callback in self.callbacks[event_name]:
                callback(value)

    """Connect to an ESPHome device and wait for state changes."""

    def _change_callback(self, state: EntityState):
        """Print the state changes of the device..."""
        if state.key in self.watched_keys:
            event_name = self.watched_keys[state.key]
            self._emit_event(event_name, state.state)

    async def _on_connect(self) -> None:
        self.logger.info("Connected to esp")
        try:
            entity_infos, services = await self.cli.list_entities_services()
            print(entity_infos, services)

            # Get keys for sensors we want to listen to
            for object_id in self._object_ids_to_find:
                entity = next(
                    (x for x in entity_infos if x.object_id == object_id), None
                )
                print(f"Found {object_id} with key {entity.key}")
                self.watched_keys[entity.key] = object_id

            # Get key for fan speed
            self._fan_speed_key = next(
                (x for x in entity_infos if x.object_id == "fan_speed"), None
            ).key

            # Subscribe to the state changes
            self.cli.subscribe_states(self._change_callback)

        except APIConnectionError as err:
            print(f"Error getting initial data for {self.hostname}: {err}")
            # Re-connection logic will trigger after this
            await self.cli.disconnect()
        except Exception as e:
            print(e)

    async def on_disconnect(self, expected_disconnect) -> None:
        """Run disconnect stuff on API disconnect."""
        if expected_disconnect:
            self.logger.warning("Unexpected disconnect from esp")
        else:
            self.logger.info("Disconnected from esp")

    async def on_connect_error(self, err: Exception) -> None:
        """Show connection errors."""
        self.logger.error(f"Failed to connect with error '{err}'")

    def __init__(self, logger: NevermoreLogAdapter, hostname: str):
        # Initialize variables
        self.logger = logger
        self.cli = None
        self.reconnect_logic = None
        self.hostname = hostname
        self.encryptionkey = None
        client_name = "ClientName"
        self.client_info = f"{client_name} 1.0.0.1"
        self.password = None

    async def start(self):
        self.cli = APIClient(
            self.hostname,
            6053,
            self.password,
            client_info=self.client_info,
            noise_psk=self.encryptionkey,
        )

        self.reconnect_logic = ReconnectLogic(
            client=self.cli,
            on_connect=self._on_connect,
            on_disconnect=self.on_disconnect,
            on_connect_error=self.on_connect_error,
        )

        await self.reconnect_logic.start()

    async def disconnect(self):
        self.logger.debug(f"Disconnecting client {self.hostname}")
        await self.reconnect_logic.stop()
        await self.cli.disconnect()
