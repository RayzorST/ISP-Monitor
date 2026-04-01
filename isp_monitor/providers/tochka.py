"""Провайдер Точка Связи (cabinet.point.online API)."""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import aiohttp

from ..base import BaseProvider, AccountInfo, AuthenticationError, NetworkError


class TochkaProvider(BaseProvider):
    """Провайдер Точка Связи.
    
    Использует официальное API: https://cabinet.point.online/customer_api
    
    Для работы требуется:
    - Логин: номер лицевого счета
    - Пароль: пароль от личного кабинета
    
    Пример использования:
        provider = TochkaProvider(login="15595492", password="your_password")
        async with provider:
            info = await provider.get_account_info()
            print(f"Баланс: {info.balance}")
    """
    
    provider_id = "tochka"
    provider_name = "Точка Связи"
    
    BASE_URL = "https://cabinet.point.online/customer_api"
    LOGIN_URL = f"{BASE_URL}/login"
    PROFILE_URL = f"{BASE_URL}/auth/profile"
    
    def __init__(self, login: str, password: str, **kwargs):
        super().__init__(login, password, **kwargs)
        self._session: Optional[aiohttp.ClientSession] = None
        self._authenticated = False
        self._profile_data: Optional[Dict[str, Any]] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получить или создать HTTP сессию."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Content-Type": "application/json",
                }
            )
        return self._session
    
    async def authenticate(self) -> bool:
        """Аутентификация в личном кабинете Точки через API."""
        if not self.validate_credentials():
            raise AuthenticationError("Неверные учетные данные")
        
        try:
            session = await self._get_session()
            
            # Отправляем запрос на авторизацию
            auth_data = {
                "login": self.login,
                "password": self.password,
            }
            
            async with session.post(
                self.LOGIN_URL,
                json=auth_data,
                timeout=10
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise AuthenticationError(
                        f"Ошибка авторизации ({response.status}): {error_text}"
                    )
                
                # Парсим ответ
                result = await response.json()
                
                # Проверяем успешность входа
                if isinstance(result, dict) and result.get("id"):
                    self._authenticated = True
                    return True
                else:
                    raise AuthenticationError("Неверный логин или пароль")
                
        except aiohttp.ClientError as e:
            raise NetworkError(f"Ошибка сети: {str(e)}")
        except asyncio.TimeoutError:
            raise NetworkError("Таймаут подключения")
        except Exception as e:
            raise AuthenticationError(f"Ошибка авторизации: {str(e)}")
    
    async def get_account_info(self) -> AccountInfo:
        """Получить информацию о балансе из профиля."""
        if not self._authenticated:
            await self.authenticate()
        
        try:
            session = await self._get_session()
            
            # Получаем данные профиля
            async with session.get(
                self.PROFILE_URL,
                timeout=10
            ) as response:
                if response.status != 200:
                    # Если сессия истекла, пробуем переавторизоваться
                    if response.status == 401:
                        self._authenticated = False
                        await self.authenticate()
                        # Повторяем запрос после переавторизации
                        async with session.get(
                            self.PROFILE_URL,
                            timeout=10
                        ) as retry_response:
                            if retry_response.status != 200:
                                raise NetworkError(
                                    f"Ошибка получения данных профиля: {retry_response.status}"
                                )
                            response = retry_response
                    
                    if response.status != 200:
                        raise NetworkError(
                            f"Ошибка получения данных профиля: {response.status}"
                        )
                
                data = await response.json()
                self._profile_data = data
                
                # Извлекаем баланс из основного поля
                balance = float(data.get("balance", 0))
                
                # Извлекаем информацию о тарифе
                service_name = ""
                tariffs = data.get("tariffs", [])
                if tariffs and len(tariffs) > 0:
                    service_name = tariffs[0].get("name", "")
                
                # Если есть аккаунты с услугами, берем оттуда
                accounts = data.get("accounts", [])
                if accounts and len(accounts) > 0:
                    account_data = accounts[0]
                    services = account_data.get("services", [])
                    if services and len(services) > 0:
                        # Берем первую услугу как основную
                        service_name = services[0].get("name", service_name)
                
                # Номер лицевого счета
                account_id = str(data.get("id", self.login))
                
                return AccountInfo(
                    balance=balance,
                    currency="RUB",
                    service_name=service_name,
                    account_id=account_id,
                    last_updated=datetime.now(),
                )
                
        except aiohttp.ClientError as e:
            raise NetworkError(f"Ошибка сети: {str(e)}")
        except asyncio.TimeoutError:
            raise NetworkError("Таймаут подключения")
        except (KeyError, ValueError, TypeError) as e:
            raise NetworkError(f"Ошибка парсинга данных: {str(e)}")
    
    async def close(self) -> None:
        """Закрыть сессию."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        self._authenticated = False
