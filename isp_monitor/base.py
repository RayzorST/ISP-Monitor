"""ISP Monitor - Модуль для отслеживания баланса интернет-провайдеров в Home Assistant."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class AccountInfo:
    """Информация о состоянии счета."""
    
    balance: float  # Баланс в рублях
    currency: str = "RUB"  # Валюта
    service_name: str = ""  # Название услуги/тарифа
    account_id: str = ""  # Идентификатор лицевого счета
    last_updated: Optional[datetime] = None  # Время последнего обновления
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь для Home Assistant."""
        return {
            "balance": self.balance,
            "currency": self.currency,
            "service_name": self.service_name,
            "account_id": self.account_id,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class ProviderError(Exception):
    """Базовое исключение для ошибок провайдера."""
    pass


class AuthenticationError(ProviderError):
    """Ошибка аутентификации."""
    pass


class NetworkError(ProviderError):
    """Ошибка сети."""
    pass


class BaseProvider(ABC):
    """Базовый класс для всех провайдеров.
    
    Все конкретные провайдеры должны наследоваться от этого класса
    и реализовать абстрактные методы.
    """
    
    # Уникальный идентификатор провайдера (например, 'tochka', 'mts', 'beeline')
    provider_id: str = ""
    
    # Человекочитаемое название провайдера
    provider_name: str = ""
    
    def __init__(self, login: str, password: str, **kwargs):
        """Инициализация провайдера.
        
        Args:
            login: Логин для входа в личный кабинет
            password: Пароль для входа в личный кабинет
            **kwargs: Дополнительные параметры, специфичные для провайдера
        """
        self.login = login
        self.password = password
        self.extra_params = kwargs
        self._session = None
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Аутентификация в личном кабинете провайдера.
        
        Returns:
            bool: True если аутентификация успешна, иначе False
            
        Raises:
            AuthenticationError: Если неверные учетные данные
            NetworkError: Если проблемы с сетью
        """
        pass
    
    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """Получить информацию о состоянии счета.
        
        Returns:
            AccountInfo: Информация о счете
            
        Raises:
            AuthenticationError: Если не аутентифицирован
            NetworkError: Если проблемы с сетью
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Закрыть сессию и освободить ресурсы."""
        pass
    
    async def __aenter__(self):
        """Контекстный менеджер для входа."""
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер для выхода."""
        await self.close()
    
    def validate_credentials(self) -> bool:
        """Проверить корректность учетных данных.
        
        Может быть переопределен в подклассах для специфичной валидации.
        
        Returns:
            bool: True если данные корректны
        """
        return bool(self.login and self.password)
