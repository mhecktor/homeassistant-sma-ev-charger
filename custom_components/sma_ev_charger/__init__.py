import asyncio
from dataclasses import dataclass
from datetime import timedelta
import logging

from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SMAEvChargerApiClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_HOST,
    CONF_SELECTED_DEVICES,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import SMAEvChargerDataUpdateCoordinator
from .api import SMAEvDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    hass.states.async_set(f"{DOMAIN}.interval", 30)

    # Return boolean to indicate that initialization was successful.
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SMA EV Charger from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)
    api = SMAEvChargerApiClient(hass, entry)

    coordinators: list[SMAEvChargerDataUpdateCoordinator] = []

    for device in hass_data[CONF_SELECTED_DEVICES]:
        coordinator = SMAEvChargerDataUpdateCoordinator(
            hass,
            entry,
            SMAEvDevice(
                component_id=device["component_id"],
                name=device["name"],
                component_type=device["component_type"],
            ),
            api,
        )
        await coordinator._async_setup()
        coordinators.append(coordinator)

    entry.runtime_data = coordinators

    await asyncio.gather(
        *[
            coordinator.async_config_entry_first_refresh()
            for coordinator in coordinators
        ]
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Remove config entry from domain.
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        # Remove options_update_listener.
        entry_data["unsub_options_update_listener"]()

    return unload_ok
