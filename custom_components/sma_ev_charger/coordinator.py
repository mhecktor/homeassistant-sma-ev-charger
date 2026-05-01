from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import SMAEvChargerApiClient, SMAEvDevice, SMAEvDeviceDetails
from .const import DOMAIN

__all__ = ["SMAEvChargerDataUpdateCoordinator"]

_LOGGER = logging.getLogger(__name__)


class SMAEvChargerDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching data from the SMA EV Charger API."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        device: SMAEvDevice,
        api: SMAEvChargerApiClient,
    ):
        """Initialize the coordinator."""
        _LOGGER.warning(
            "Initializing SMAEvChargerDataUpdateCoordinator for device %s with ID %s on the interface %s",
            device.name,
            device.component_id,
            config_entry.options.get(CONF_SCAN_INTERVAL, 30),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            always_update=False,
            update_interval=timedelta(
                seconds=config_entry.options.get(CONF_SCAN_INTERVAL, 30)
            ),
        )
        self.device = device
        self.device_details: SMAEvDeviceDetails | None = None
        self.api = api

    async def update_device_details(self):
        """Fetch device details from the API and update the device information."""
        self.device_details = await self.api.get_device_details(
            self.device.component_id
        )

    async def _async_setup(self):
        """Set up the coordinator."""
        await self.update_device_details()
        # self.devices = await self.api.async_get_home_appliances()

    async def _async_update_data(self):
        """Fetch data from the API."""

        emobility = await self.api.async_get_emobility(
            component_id=self.device.component_id
        )
        return {
            "emobility": emobility,
        }

        # self.api.get
