#!/usr/bin/env python3
"""Тестовый скрипт для проверки импортов"""

try:
    from src.config.settings import load_config, init_config
    print("✓ Конфигурация импортирована")
    
    from src.services.api_client import APIClient
    print("✓ API клиент импортирован")
    
    from src.services.telegram_service import TelegramService
    print("✓ Telegram сервис импортирован")
    
    from src.utils.formatters import format_datetime
    print("✓ Форматтеры импортированы")
    
    from src.utils.file_manager import load_sent_orders
    print("✓ Файловый менеджер импортирован")
    
    from src.core.monitor import MagistraliMonitor
    print("✓ Монитор импортирован")
    
    print("\n✅ Все импорты работают корректно!")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
except Exception as e:
    print(f"❌ Другая ошибка: {e}")