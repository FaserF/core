from homeassistant.components.update import UpdateEntity
from homeassistant.const import CONF_NAME, CONF_TOPIC
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import asyncio
import requests
import logging
from datetime import timedelta
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class TasmotaUpdateEntity(UpdateEntity):
    """Represents a Tasmota firmware update."""

    def __init__(self, name, installed_version, latest_version, tasmota_mqtt, topic):
        """Initialize the update entity."""
        self._attr_name = f"{name} Firmware Update"
        self._attr_installed_version = installed_version
        self._attr_latest_version = latest_version
        self._tasmota_mqtt = tasmota_mqtt
        self._topic = topic

    @property
    def title(self):
        return self._attr_name

    @property
    def installed_version(self):
        return self._attr_installed_version

    @property
    def latest_version(self):
        return self._attr_latest_version

    async def install(self, version=None, backup=False):
        """Trigger the installation of a new firmware version."""
        await install_firmware_update(self._tasmota_mqtt, self._topic)

async def install_firmware_update(tasmota_mqtt, topic):
    """Trigger the firmware update via MQTT."""
    await tasmota_mqtt.publish(f"{topic}/cmnd/Upgrade", "1")

async def get_installed_version(tasmota_mqtt, topic):
    """Fetch the installed firmware version from the Tasmota device."""
    # Use the correct method to get the installed version via MQTT
    response = await tasmota_mqtt.publish(f"{topic}/cmnd/STATUS2", "")
    # Here you should process the response and extract the version
    return response["StatusFWR"]["Version"]

async def get_latest_version():
    """Fetch the latest firmware version from GitHub."""
    url = "https://api.github.com/repos/arendst/Tasmota/releases/latest"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data["tag_name"].lstrip("v")
    except Exception as err:
        _LOGGER.error(f"Error fetching the latest firmware: {err}")
        return None

async def async_update_firmware_info(tasmota_mqtt, topic):
    """Update the firmware info from the Tasmota device."""
    # Fetch the current version from the device
    current_version = await get_installed_version(tasmota_mqtt, topic)
    
    # Fetch the latest version from GitHub
    latest_version = await get_latest_version()
    
    # Update the entity attributes
    if current_version and latest_version:
        return TasmotaUpdateEntity(
            name="Tasmota Firmware Update",
            installed_version=current_version,
            latest_version=latest_version,
            tasmota_mqtt=tasmota_mqtt,
            topic=topic,
        )
    return None
