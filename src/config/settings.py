import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Глобальная переменная для конфигурации
_CONFIG = None

def load_config(config_path: str = "config.json") -> dict:
    """Загрузка конфигурации из JSON файла"""
    global _CONFIG
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file {config_path} not found")
            
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            
        _CONFIG = {
            "API_BASE_URL": config_data.get("API_BASE_URL", "https://yamagistrali.ru"),
            "TELEGRAM_BOT_TOKEN": config_data.get("TELEGRAM_BOT_TOKEN"),
            "TELEGRAM_CHANNEL_ID": config_data.get("TELEGRAM_CHANNEL_ID"),
            "STATIC_TOKEN": config_data.get("STATIC_TOKEN"),
            "POLLING_INTERVAL": config_data.get("POLLING_INTERVAL", 300),
            "LOOKBACK_PERIOD_HOURS": config_data.get("LOOKBACK_PERIOD_HOURS", 24),
            "MAX_CACHED_ORDERS": config_data.get("MAX_CACHED_ORDERS", 200)
        }
        
        return _CONFIG
        
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise

def get_config() -> dict:
    """Получение конфигурации"""
    if _CONFIG is None:
        raise RuntimeError("Configuration not initialized. Call load_config() first.")
    return _CONFIG

def init_config(config_path: str = "config.json"):
    """Инициализация конфигурации"""
    return load_config(config_path)