import logging
from typing import Any

from aioesphomeapi import SensorStateClass
from bluemaestro_ble import SensorDeviceClass

from .coordinator import SMAEvChargerDataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .entity import BaseEntity

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    StateType,
    cached_property,
)

_LOGGER = logging.getLogger(__name__)


def get_device_handlers(
    coordinator: SMAEvChargerDataUpdateCoordinator,
):
    return {
        "Device": [
            EnergyConsumptionSensor(coordinator),
            ChargeStatusSensor(coordinator),
            PowerSensor(coordinator),
        ]
    }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    # coordinator = entry.runtime_data.coordinator
    _LOGGER.warning(
        "Setting up sensor platform with coordinator %s",
        entry.entry_id,
        extra=entry.data,
    )

    entities = []

    for coordinator in entry.runtime_data:
        device_handlers = get_device_handlers(coordinator)
        device_type = coordinator.device.component_type
        _LOGGER.warning(
            "Found device of type %s with ID %s",
            device_type,
            coordinator.device.component_id,
        )

        for device_class, entity in device_handlers.items():
            if device_type == device_class:
                entities.extend(entity)

    async_add_entities(entities)


class PowerSensor(BaseEntity, SensorEntity):
    """Sensor for EV charger power usage."""

    _attr_icon = "mdi:flash"
    _attr_native_unit_of_measurement = UnitOfPower["WATT"]
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.POWER

    def get_native_value(self) -> StateType | float:
        """Calculate the native value for power usage."""
        power: list[dict[str, Any]] = self.coordinator.data.get("emobility", {}).power
        return power

    def __init__(
        self,
        coordinator: SMAEvChargerDataUpdateCoordinator,
    ) -> None:
        super().__init__(coordinator, feature_id="power_usage")
        self.entity_description = SensorEntityDescription(
            key="power_usage",
            name="Current Power",
            icon="mdi:flash",
            native_unit_of_measurement=UnitOfPower["WATT"],
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.POWER,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._attr_native_value = self.get_native_value()
        self.async_write_ha_state()

    @cached_property
    def native_value(self) -> StateType | float:
        return self.get_native_value()


class EnergyConsumptionSensor(BaseEntity, SensorEntity):
    """Sensor for EV charger energy usage."""

    # _attr_native_unit_of_measurement = UnitOfEnergy["WATT_HOUR"]
    # _attr_state_class = SensorStateClass.TOTAL_INCREASING
    # _attr_device_class = SensorDeviceClass.ENERGY

    def get_native_value(self) -> StateType | float:
        """Calculate the native value for water usage."""
        session_energy: list[dict[str, Any]] = self.coordinator.data.get(
            "emobility", {}
        ).session_energy
        return session_energy

    def __init__(
        self,
        coordinator: SMAEvChargerDataUpdateCoordinator,
    ) -> None:
        super().__init__(coordinator, feature_id="energy_consumption")
        self.entity_description = SensorEntityDescription(
            key="energy_consumption",
            name="Session Energy Consumption",
            icon="mdi:ev-station",
            native_unit_of_measurement=UnitOfEnergy["WATT_HOUR"],
            state_class=SensorStateClass.TOTAL_INCREASING,
            device_class=SensorDeviceClass.ENERGY,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._attr_native_value = self.get_native_value()
        self.async_write_ha_state()

    @cached_property
    def native_value(self) -> StateType | float:
        return self.get_native_value()


class ChargeStatusSensor(BaseEntity, SensorEntity):
    """Sensor for EV charger charge status."""

    _attr_icon = "mdi:connection"

    def get_native_value(self) -> StateType | float:
        """Calculate the native value for charge status."""
        charge_status: list[dict[str, Any]] = self.coordinator.data.get(
            "emobility", {}
        ).charge_status
        return charge_status

    def __init__(
        self,
        coordinator: SMAEvChargerDataUpdateCoordinator,
    ) -> None:
        super().__init__(coordinator, feature_id="charge_status")
        self.entity_description = SensorEntityDescription(
            key="charge_status", name="Charge Status", icon="mdi:connection"
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._attr_native_value = self.get_native_value()
        self.async_write_ha_state()

    @cached_property
    def native_value(self) -> StateType | float:
        return self.get_native_value()
