from datetime import timedelta
from typing import Any

import voluptuous as vol

from homeassistant import config_entries

from .const import CONF_SCAN_INTERVAL

__all__ = ["SMAEvChargerOptionsFlow"]

DURATION_REGEX = r"^\d{2}:\d{2}:\d{2}$"


def _parse_timedelta(value: str) -> timedelta:
    parts = value.split(":")
    if len(parts) != 3:
        raise ValueError("Invalid format")

    hours, minutes, seconds = parts

    try:
        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)
    except ValueError as err:
        raise ValueError("Not integers") from err

    if minutes < 0 or minutes >= 60 or seconds < 0 or seconds >= 60:
        raise ValueError("Invalid range")

    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


class SMAEvChargerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for SMA EV Charger integration."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options for the custom component."""
        errors: dict[str, str] = {}

        if user_input is not None:
            duration_str = user_input[CONF_SCAN_INTERVAL]
            try:
                parsed = _parse_timedelta(duration_str)
                return self.async_create_entry(
                    data={CONF_SCAN_INTERVAL: parsed.total_seconds()},
                )
            except ValueError:
                errors[CONF_SCAN_INTERVAL] = "invalid_scan_interval"

        current_seconds = self.config_entry.options.get(CONF_SCAN_INTERVAL, 300)
        current_str = str(timedelta(seconds=current_seconds))[:8].zfill(
            8
        )  # e.g. "00:05:00"

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=current_str
                ): str,  # ✅ serializable — cv.time_period_str was not
            }
        )

        # Show the options form
        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
        )
