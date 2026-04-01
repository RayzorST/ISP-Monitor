"""Интеграция ISP Monitor для Home Assistant."""

import logging
from datetime import timedelta
from typing import Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_PROVIDER, PLATFORMS
from .providers.base import BaseProvider, AccountInfo, AuthenticationError, NetworkError
from .providers import PointProvider

_LOGGER = logging.getLogger(__name__)

# Схема конфигурации для UI
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_PROVIDER, default="Point"): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Настройка компонента из YAML (если используется)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Настройка интеграции из Config Entry (UI)."""
    
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    provider_id = entry.data.get(CONF_PROVIDER, "Point")
    
    # Создаем экземпляр провайдера
    provider = create_provider(provider_id, username, password)
    
    if not provider:
        _LOGGER.error("Неизвестный провайдер: %s", provider_id)
        return False
    
    # Создаем координатор данных
    coordinator = ISPMonitorCoordinator(hass, provider, entry)
    
    # Пробуем получить данные первый раз
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        await provider.close()
        raise
    except Exception as err:
        await provider.close()
        raise ConfigEntryNotReady(f"Ошибка подключения к провайдеру: {err}") from err
    
    # Сохраняем координатор
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    
    # Настраиваем платформы
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Выгрузка интеграции."""
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator: ISPMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.provider.close()
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


def create_provider(provider_id: str, login: str, password: str, **kwargs) -> Optional[BaseProvider]:
    """Фабрика для создания провайдеров.
    
    Args:
        provider_id: Идентификатор провайдера ('Point', 'mts', etc.)
        login: Логин
        password: Пароль
        **kwargs: Дополнительные параметры
        
    Returns:
        Экземпляр провайдера или None если не найден
    """
    providers_map = {
        "point": PointProvider,
        # Здесь можно добавлять других провайдеров
        # "mts": MTSProvider,
        # "beeline": BeelineProvider,
    }
    
    provider_class = providers_map.get(provider_id)
    
    if provider_class:
        return provider_class(login=login, password=password, **kwargs)
    
    return None


class ISPMonitorCoordinator(DataUpdateCoordinator[AccountInfo]):
    """Координатор данных для обновления информации о счете."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        provider: BaseProvider,
        config_entry: ConfigEntry,
    ):
        super().__init__(
            hass,
            _LOGGER,
            name=f"ISP Monitor ({provider.provider_name})",
            update_interval=timedelta(hours=1),  # Обновление каждый час
        )
        
        self.provider = provider
        self.config_entry = config_entry
    
    async def _async_update_data(self) -> AccountInfo:
        """Обновление данных."""
        try:
            account_info = await self.provider.get_account_info()
            return account_info
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed(f"Ошибка аутентификации: {err}") from err
        except NetworkError as err:
            raise UpdateFailed(f"Ошибка сети: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Неизвестная ошибка: {err}") from err
