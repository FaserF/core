"""Support for Tasmota updates."""

from __future__ import annotations

from typing import Any

from hatasmota import update as tasmota_update
from hatasmota.entity import TasmotaEntity as HATasmotaEntity
from hatasmota.models import DiscoveryHashType

from homeassistant.components import update
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_REMOVE_DISCOVER_COMPONENT
from .discovery import TASMOTA_DISCOVERY_ENTITY_NEW
from .entity import TasmotaAvailability, TasmotaDiscoveryUpdate, TasmotaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Tasmota update dynamically through discovery."""

    @callback
    def async_discover(
        tasmota_entity: HATasmotaEntity, discovery_hash: DiscoveryHashType
    ) -> None:
        """Discover and add a Tasmota update."""
        async_add_entities(
            [
                TasmotaUpdateEntity(
                    tasmota_entity=tasmota_entity, discovery_hash=discovery_hash
                )
            ]
        )

    hass.data[DATA_REMOVE_DISCOVER_COMPONENT.format(update.DOMAIN)] = (
        async_dispatcher_connect(
            hass,
            TASMOTA_DISCOVERY_ENTITY_NEW.format(update.DOMAIN),
            async_discover,
        )
    )


class TasmotaUpdateEntity(
    TasmotaAvailability,
    TasmotaDiscoveryUpdate,
    TasmotaEntity,
    UpdateEntity,
):
    """Representation of a Tasmota update."""

    _tasmota_entity: tasmota_update.TasmotaUpdate

    def __init__(self, **kwds: Any) -> None:
        """Initialize."""
        super().__init__(**kwds)
        self._attr_supported_features = (
            UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS
        )
        self._attr_title = "Firmware"
        self._attr_installed_version = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to Tasmota updates."""
        await super().async_added_to_hass()
        self._tasmota_entity.set_on_state_callback(self._on_state_callback)
        await self._tasmota_entity.poll_status()

    @callback
    def _on_state_callback(self, version: str) -> None:
        """Update the version."""
        self._attr_installed_version = version
        # We don't know the latest version, so we assume it matches unless we implement
        # a check against a repo. For generic Tasmota usage, sticking to installed_version
        # allows 'install' to be triggered without reporting new version if we want to
        # just allow "reinstall/upgrade" blindly.
        # But UpdateEntity usually requires latest_version != installed_version to show update available.
        # If we just want to allow user to trigger "Upgrade 1", we might need to fake latest info
        # or leave as is.
        # Requirement: "make it universal compatible".
        # If we leave latest_version as None, HA shows "Unknown".
        # If we set it to installed_version, HA says "Up to date".
        # But we want to allow "Update".
        # Maybe we can just allow install.
        self.async_write_ha_state()

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Install an update."""
        # Tasmota 'Upgrade 1' command upgrades to latest available via OTA Url.
        await self._tasmota_entity.update_firmware()
