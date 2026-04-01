"""Пример использования ISP Monitor."""

import asyncio
from isp_monitor.base import AccountInfo
from isp_monitor.providers import TochkaProvider


async def main():
    """Пример использования провайдера Точка Связи.
    
    Для работы требуется:
    - Логин: номер лицевого счета (например, 15595492)
    - Пароль: пароль от личного кабинета
    
    API провайдера:
    - Авторизация: POST https://cabinet.point.online/customer_api/login
    - Профиль: GET https://cabinet.point.online/customer_api/auth/profile
    
    Формат запроса на авторизацию:
    {
        "login": "15595492",
        "password": "your_password"
    }
    """
    
    # Замените на ваши реальные данные
    LOGIN = "your_login"
    PASSWORD = "your_password"
    
    # Создаем экземпляр провайдера
    provider = TochkaProvider(login=LOGIN, password=PASSWORD)
    
    try:
        # Аутентификация и получение данных
        async with provider:
            info: AccountInfo = await provider.get_account_info()
            
            print(f"Баланс: {info.balance} {info.currency}")
            print(f"Лицевой счет: {info.account_id}")
            print(f"Тариф: {info.service_name}")
            print(f"Обновлено: {info.last_updated}")
            
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
