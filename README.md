# ISP Monitor

Модульная система для отслеживания баланса интернет-провайдеров в Home Assistant.

## Возможности

- ✅ Модульная архитектура с базовым интерфейсом
- ✅ Легкое добавление новых провайдеров
- ✅ Готовая интеграция для Home Assistant
- ✅ Настройка через UI (Config Flow)
- ✅ Сенсоры баланса с автообновлением

## Структура проекта

```
isp_monitor/
├── base.py                 # Базовый интерфейс и общие классы
├── providers/              # Конкретные реализации провайдеров
│   ├── __init__.py
│   └── point.py          # Провайдер "Точка Связи"
├── integration/            # Интеграция для Home Assistant
│   ├── __init__.py        # Основная логика интеграции
│   ├── config_flow.py     # Настройка через UI
│   ├── const.py           # Константы
│   ├── manifest.json      # Манифест HA
│   ├── sensor.py          # Сенсор баланса
│   └── strings.json       # Локализация
└── example.py             # Пример использования
```

## Установка

### Как библиотека Python

```bash
pip install -e .
```

### Как интеграция Home Assistant

1. Скопируйте папку `integration` в `custom_components` вашего HA:
   ```bash
   cp -r isp_monitor/integration ~/.homeassistant/custom_components/isp_monitor
   ```

2. Перезапустите Home Assistant

3. Добавьте интеграцию через UI:
   - Настройки → Устройства и службы → Добавить интеграцию
   - Найдите "ISP Monitor"
   - Выберите провайдера и введите учетные данные

## Использование как библиотеки

```python
import asyncio
from isp_monitor.providers import PointProvider

async def main():
    provider = PointProvider(login="your_login", password="your_password")
    
    async with provider:
        info = await provider.get_account_info()
        print(f"Баланс: {info.balance} {info.currency}")

asyncio.run(main())
```

## Добавление нового провайдера

1. Создайте новый файл в `providers/`:

```python
# providers/myprovider.py
from ..base import BaseProvider, AccountInfo, AuthenticationError, NetworkError

class MyProvider(BaseProvider):
    provider_id = "myprovider"
    provider_name = "Мой Провайдер"
    
    async def authenticate(self) -> bool:
        # Реализуйте логику аутентификации
        pass
    
    async def get_account_info(self) -> AccountInfo:
        # Реализуйте получение данных о балансе
        pass
    
    async def close(self) -> None:
        # Очистка ресурсов
        pass
```

2. Зарегистрируйте провайдер в `providers/__init__.py`:

```python
from .myprovider import MyProvider

__all__ = ["PointProvider", "MyProvider"]
```

3. Добавьте в фабрику `integration/__init__.py`:

```python
providers_map = {
    "Point": PointProvider,
    "myprovider": MyProvider,
}
```

4. Обновите список в `integration/config_flow.py`:

```python
PROVIDERS = {
    "Point": "Точка Связи",
    "myprovider": "Мой Провайдер",
}
```

## Требования

- Python 3.9+
- aiohttp >= 3.8.0

## Лицензия

MIT
