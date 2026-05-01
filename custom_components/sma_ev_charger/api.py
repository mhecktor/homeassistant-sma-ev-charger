"""API client for SMA EV Charger integration."""

from dataclasses import dataclass
import logging
import time
from types import MappingProxyType
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_ACCESS_TOKEN, CONF_EXPIRES_AT, CONF_HOST, CONF_REFRESH_TOKEN

_LOGGER = logging.getLogger(__name__)


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate invalid auth."""

    def __init__(self, message: str | None = None) -> None:
        self.message = message or "Invalid authentication"
        super().__init__(self.message)


@dataclass
class SMAEvDevice:
    """Represents a device connected to the SMA EV Charger."""

    component_id: str
    component_type: str
    name: str


@dataclass
class SMAEvDeviceDetails:
    """Represents detailed information about a device connected to the SMA EV Charger."""

    device_id: str
    firmware_version: str
    ip_address: str
    name: str
    serial_number: str
    vendor: str
    product: str


@dataclass
class SMAEvDeviceEmobility:
    """Represents emobility information about a device connected to the SMA EV Charger."""

    charge_status: str
    power: float
    session_energy: float


async def async_refresh_token(
    base_url: str,
    refresh_token: str,
) -> dict[str, Any]:
    """Refresh an OAuth access token."""

    url = f"https://{base_url.rstrip('/')}/api/v1/token"

    payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        async with (
            aiohttp.ClientSession() as session,
            session.post(url, data=payload, headers=headers, ssl=False) as response,
        ):
            if response.status in (400, 401, 403):
                response_message = await response.text()
                _LOGGER.error(
                    "Invalid auth response [%s]: %s",
                    response.status,
                    response_message,
                )
                raise InvalidAuth(response_message)

            response.raise_for_status()
            token_data = await response.json()

    except InvalidAuth:
        raise
    except aiohttp.ClientError as err:
        raise CannotConnect from err

    if "access_token" not in token_data:
        raise InvalidAuth

    return token_data


class SMAEvChargerApiClient:
    """API client for SMA EV Charger."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ):
        self.hass = hass
        self.entry = entry

    @property
    def data(self) -> MappingProxyType[str, Any]:
        return self.entry.data

    def get_auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.entry.data[CONF_ACCESS_TOKEN]}"}

    @staticmethod
    async def async_get_access_token(
        host: str, username: str, password: str
    ) -> dict[str, Any]:
        url = f"https://{host.rstrip('/')}/api/v1/token"

        payload = {
            "grant_type": "password",
            "password": password,
            "username": username,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        async with (
            aiohttp.ClientSession() as session,
            session.post(url, data=payload, headers=headers, ssl=False) as response,
        ):
            if response.status in (400, 401, 403):
                response_message = await response.text()
                _LOGGER.error(
                    "Invalid auth response [%s]: %s",
                    response.status,
                    response_message,
                )
                raise InvalidAuth(response_message)

            response.raise_for_status()
            token_data = await response.json()
        return token_data

    async def async_refresh_token(self) -> None:
        token_data = await async_refresh_token(
            base_url=self.data[CONF_HOST],
            refresh_token=self.data[CONF_REFRESH_TOKEN],
        )

        new_data = dict(self.data)
        new_data[CONF_ACCESS_TOKEN] = token_data["access_token"]
        new_data[CONF_REFRESH_TOKEN] = token_data.get(
            "refresh_token",
            self.data[CONF_REFRESH_TOKEN],
        )
        new_data[CONF_EXPIRES_AT] = time.time() + token_data.get("expires_in", 3600)

        self.hass.config_entries.async_update_entry(
            self.entry,
            data=new_data,
        )

    @staticmethod
    async def async_get_plant_id_static(host: str, access_token: str) -> str:
        url = f"https://{host.rstrip('/')}/api/v1/navigation/menuitems"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with aiohttp.ClientSession() as session:
            response = await session.get(url, headers=headers, ssl=False)
            response.raise_for_status()
            data = await response.json()
            plant_id = data["componentId"]
        return plant_id

    async def async_get_plant_id(self) -> str:
        await self.async_refresh_token()
        return await SMAEvChargerApiClient.async_get_plant_id_static(
            host=self.data[CONF_HOST],
            access_token=self.data[CONF_ACCESS_TOKEN],
        )

    @staticmethod
    async def async_get_devices_static(
        host: str, access_token: str, plant_id: str
    ) -> list[SMAEvDevice]:
        url = f"https://{host.rstrip('/')}/api/v1/navigation?parentId={plant_id}"
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                url, headers={"Authorization": f"Bearer {access_token}"}, ssl=False
            )
            response.raise_for_status()
            devices = await response.json()

        return [
            SMAEvDevice(
                component_id=device["componentId"],
                component_type=device["componentType"],
                name=device["name"],
            )
            for device in devices
        ]

    async def async_get_devices(self, plant_id: str) -> list[SMAEvDevice]:
        await self.async_refresh_token()
        return await SMAEvChargerApiClient.async_get_devices_static(
            host=self.data[CONF_HOST],
            access_token=self.data[CONF_ACCESS_TOKEN],
            plant_id=plant_id,
        )

    async def get_device_details(self, component_id: str) -> SMAEvDeviceDetails:
        url = f"https://{self.data[CONF_HOST].rstrip('/')}/api/v1/plants/Plant:1/devices/{component_id}"
        async with (
            aiohttp.ClientSession() as session,
            session.get(url, headers=self.get_auth_headers(), ssl=False) as response,
        ):
            response.raise_for_status()
            device_details = await response.json()

        return SMAEvDeviceDetails(
            device_id=device_details["deviceId"],
            firmware_version=device_details["firmwareVersion"],
            ip_address=device_details["ipAddress"],
            name=device_details["name"],
            serial_number=device_details["serial"],
            vendor=device_details["vendor"],
            product=device_details["product"],
        )

    async def async_get_device_measurements(self, component_id: str) -> dict[str, Any]:
        url = f"https://{self.data[CONF_HOST].rstrip('/')}/api/v1/plants/Plant:1/devices/{component_id}/measurements"
        payload = {
            "queryItems": [
                {
                    "componentId": component_id,
                    "channelId": "Measurement.Metering.GridMs.TotWhIn",
                    "resolution": "OneDay",
                    "timezone": "Europe/Berlin",
                    "aggregate": "Dif",
                    "multiAggregate": "Sum",
                },
                {
                    "componentId": component_id,
                    "channelId": "Measurement.Metering.GridMs.TotWhOut",
                    "resolution": "OneDay",
                    "timezone": "Europe/Berlin",
                    "aggregate": "Dif",
                    "multiAggregate": "Sum",
                },
            ],
            "dateTimeBegin": time.strftime(
                "%Y-%m-%dT00:00:00.000Z", time.gmtime(time.time() - 24 * 3600)
            ),
            "dateTimeEnd": time.strftime(
                "%Y-%m-%dT00:00:00.000Z", time.gmtime(time.time())
            ),
        }
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                url, headers=self.get_auth_headers(), ssl=False
            )
            response.raise_for_status()
            measurements = await response.json()

        return measurements

    async def async_get_emobility(self, component_id: str) -> dict[str, Any]:
        await self.async_refresh_token()

        url = f"https://{self.data[CONF_HOST].rstrip('/')}/api/v1/widgets/emobility?componentId={component_id}"
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                url, headers=self.get_auth_headers(), ssl=False
            )
            response.raise_for_status()
            emobility_data = await response.json()

        return SMAEvDeviceEmobility(
            charge_status=emobility_data["chargeStatus"],
            power=emobility_data["power"],
            session_energy=emobility_data["sessionEnergy"],
        )
