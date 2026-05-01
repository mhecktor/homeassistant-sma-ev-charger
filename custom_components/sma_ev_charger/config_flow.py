"""Config flow for SMA EV Charger integration."""

import logging
import time
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .api import InvalidAuth, SMAEvChargerApiClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_EXPIRES_AT,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_REFRESH_TOKEN,
    CONF_SELECTED_DEVICES,
    CONF_USERNAME,
    DOMAIN,
)
from .options_flow import SMAEvChargerOptionsFlow

_LOGGER = logging.getLogger(__name__)


class SmaEvChargerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SMA EV Charger."""

    def __init__(self) -> None:
        """Initialize the config flow."""
        # _LOGGER.warning(
        #     "SMA EV Charger integration is in early development. "
        #     "Expect frequent breaking changes and instability."
        # )
        self.data: dict[str, Any] = {}

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Page 1: collect api details."""

        if user_input is not None:
            self.data.update(user_input)

            return await self.async_step_device_selection()

            # return self.async_create_entry(
            #     title="SMA EV Charger",
            #     data={
            #         CONF_HOST: self.data[CONF_HOST],
            #         CONF_ACCESS_TOKEN: access_token,
            #         CONF_REFRESH_TOKEN: refresh_token,
            #         CONF_EXPIRES_AT: time.time() + expires_in,
            #     },
            # )

        errors = {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_device_selection(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Page 2: device selection."""

        if not hasattr(self, "_fetch_token"):
            self._token_error: str | None = None
            self._fetch_token = self.hass.async_create_task(self._async_fetch_token())

        if not self._fetch_token.done():
            return self.async_show_progress(
                step_id="device_selection",
                progress_action="fetching_token",
                progress_task=self._fetch_token,
            )

        # Step B: kick off background fetch on first entry
        if not hasattr(self, "_fetch_task"):
            self._fetch_error: str | None = None
            self._fetch_task = self.hass.async_create_task(self._async_fetch_devices())

        # Step C: still running → show spinner
        if not self._fetch_task.done():
            return self.async_show_progress(
                step_id="device_selection",
                progress_action="fetching_devices",
                progress_task=self._fetch_task,
            )

        # Step C: task finished — check for errors
        if self._fetch_error:
            return self.async_show_progress_done(next_step_id="device_selection_error")

        return self.async_show_progress_done(next_step_id="device_selection_form")

    async def async_step_device_selection_form(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Page 2b: actual device selection form (shown after fetch completes)."""
        all_devices = {
            d.name: d.name for d in sorted(self._devices, key=lambda x: x.name)
        }
        devices_map = {d.name: d for d in self._devices}

        if user_input is not None:
            selected_devices = [
                devices_map[entity_id] for entity_id in user_input.get("devices", [])
            ]
            return self.async_create_entry(
                title="SMA EV Charger",
                data={**self.data, CONF_SELECTED_DEVICES: selected_devices},
            )

        return self.async_show_form(
            step_id="device_selection_form",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "devices", default=list(all_devices.keys())
                    ): cv.multi_select(all_devices)
                }
            ),
        )

    async def async_step_device_selection_error(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Page 2c: shown when device fetch failed."""
        return self.async_show_form(
            step_id="device_selection_error",
            data_schema=vol.Schema({}),
            errors={"base": self._fetch_error},
        )

    async def _async_fetch_devices(self) -> None:
        """Background task: fetch plant ID and devices from the API."""
        try:
            plant_id = await SMAEvChargerApiClient.async_get_plant_id_static(
                host=self.data[CONF_HOST],
                access_token=self.data[CONF_ACCESS_TOKEN],
            )
            self._devices = await SMAEvChargerApiClient.async_get_devices_static(
                host=self.data[CONF_HOST],
                access_token=self.data[CONF_ACCESS_TOKEN],
                plant_id=plant_id,
            )
        except Exception as err:
            _LOGGER.error("Error fetching devices: %s", err, exc_info=True)
            self._fetch_error = "fetching_devices_failed"

    async def _async_fetch_token(self) -> None:
        """Background task: fetch access token from the API."""
        try:
            token_data = await SMAEvChargerApiClient.async_get_access_token(
                host=self.data[CONF_HOST],
                username=self.data[CONF_USERNAME],
                password=self.data[CONF_PASSWORD],
            )

            access_token = token_data["access_token"]
            refresh_token = token_data["refresh_token"]
            expires_in = token_data.get("expires_in", 3600)

            self.data = {
                CONF_HOST: self.data[CONF_HOST],
                CONF_ACCESS_TOKEN: access_token,
                CONF_REFRESH_TOKEN: refresh_token,
                CONF_EXPIRES_AT: time.time() + expires_in,
            }
        except InvalidAuth:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_HOST, default=self.data[CONF_HOST]): str,
                        vol.Required(
                            CONF_USERNAME, default=self.data[CONF_USERNAME]
                        ): str,
                        vol.Required(CONF_PASSWORD): str,
                    }
                ),
                errors={"base": "invalid_auth"},
            )
        except Exception as err:
            _LOGGER.error("Error fetching access token: %s", err, exc_info=True)
            self._token_error = "fetching_token_failed"

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Get the options flow for this handler."""
        return SMAEvChargerOptionsFlow()
