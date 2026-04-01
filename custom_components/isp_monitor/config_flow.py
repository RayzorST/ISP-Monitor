"""Config Flow для настройки интеграции через UI."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, CONF_PROVIDER
from .providers.base import AuthenticationError, NetworkError
from .providers import PointProvider

_LOGGER = logging.getLogger(__name__)

# Список доступных провайдеров
PROVIDERS = {
    "point": "Точка Связи",
    # Можно добавить других провайдеров
    # "mts": "МТС",
    # "beeline": "Билайн",
}


class ISPConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow для ISP Monitor."""
    
    VERSION = 1
    
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Первый шаг: выбор провайдера и ввод учетных данных."""
        
        errors = {}
        
        if user_input is not None:
            # Проверяем уникальность (один аккаунт = одна запись)
            await self.async_set_unique_id(
                f"{user_input[CONF_PROVIDER]}_{user_input[CONF_USERNAME]}"
            )
            self._abort_if_unique_id_configured()
            
            # Пробуем подключиться к провайдеру
            try:
                provider = await self._test_connection(
                    user_input[CONF_PROVIDER],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
                
                if provider:
                    return self.async_create_entry(
                        title=f"{PROVIDERS[user_input[CONF_PROVIDER]]} ({user_input[CONF_USERNAME]})",
                        data=user_input,
                    )
                    
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except NetworkError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        
        # Форма ввода данных
        data_schema = vol.Schema(
            {
                vol.Required(CONF_PROVIDER, default="Point"): vol.In(PROVIDERS),
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
    
    async def _test_connection(
        self, provider_id: str, username: str, password: str
    ) -> bool:
        """Проверка подключения к провайдеру."""
        
        if provider_id == "point":
            provider = PointProvider(login=username, password=password)
        else:
            raise ValueError(f"Unknown provider: {provider_id}")
        
        try:
            await provider.authenticate()
            return True
        finally:
            await provider.close()


class CannotConnect(HomeAssistantError):
    """Ошибка подключения."""


class InvalidAuth(HomeAssistantError):
    """Ошибка аутентификации."""
