from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import SMAEvChargerDataUpdateCoordinator
from .const import DOMAIN


class BaseEntity(CoordinatorEntity[SMAEvChargerDataUpdateCoordinator]):
    """Base entity for SMA EV Charger integration."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SMAEvChargerDataUpdateCoordinator,
        feature_id: str,
    ) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._id = coordinator.device.component_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._id)},
            name=str(coordinator.device.name),
            manufacturer=str(coordinator.device_details.vendor),
            model=str(coordinator.device_details.product),
            serial_number=str(coordinator.device_details.serial_number),
        )
        self.feature_id = feature_id
        self._attr_unique_id = f"{self._id}_{feature_id}"
