"""Сенсор для отображения баланса провайдера."""

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .providers.base import AccountInfo
from . import ISPMonitorCoordinator
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Настройка сенсоров из Config Entry."""
    
    coordinator: ISPMonitorCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Создаем сенсор баланса
    entity = ISPBalanceSensor(coordinator, config_entry)
    async_add_entities([entity], True)


class ISPBalanceSensor(CoordinatorEntity[ISPMonitorCoordinator], SensorEntity):
    """Сенсор баланса интернет-провайдера."""
    
    _attr_has_entity_name = True
    _attr_translation_key = "balance"
    
    def __init__(
        self,
        coordinator: ISPMonitorCoordinator,
        config_entry: ConfigEntry,
    ):
        super().__init__(coordinator)
        
        self.config_entry = config_entry
        self.provider = coordinator.provider
        
        # Уникальный ID
        self._attr_unique_id = f"{self.provider.provider_id}_{self.provider.login}_balance"
        
        # Название устройства
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self.provider.provider_id, self.provider.login)},
            "name": f"ISP Monitor ({self.provider.provider_name})",
            "manufacturer": self.provider.provider_name,
            "entry_type": "service",
        }
    
    @property
    def native_value(self) -> float | None:
        """Текущее значение баланса."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.balance
    
    @property
    def native_unit_of_measurement(self) -> str | None:
        """Единица измерения."""
        return self.coordinator.data.currency
    
    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Тип устройства."""
        return SensorDeviceClass.MONETARY
    
    @property
    def state_class(self) -> SensorStateClass | None:
        """Класс состояния."""
        return SensorStateClass.MEASUREMENT
    
    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Дополнительные атрибуты."""
        if self.coordinator.data is None:
            return None
        
        attrs = {
            "account_id": self.coordinator.data.account_id,
            "service_name": self.coordinator.data.service_name,
            "last_updated": self.coordinator.data.last_updated,
        }
        
        return attrs
