import json
import logging
from pathlib import Path
from typing import Set

logger = logging.getLogger(__name__)

def load_sent_orders(file_path: str = "data/sent_orders.json") -> Set[str]:
    """Загрузка сохраненных ID отправленных заказов из файла"""
    try:
        file = Path(file_path)
        
        # Создаем папку, если не существует
        file.parent.mkdir(parents=True, exist_ok=True)
        
        if not file.exists():
            # Создаем пустой файл
            save_sent_orders(set(), file_path)
            return set()
            
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return set()
                
            data = json.loads(content)
            return set(data.keys())
            
    except Exception as e:
        logger.error(f"Error loading sent orders: {str(e)}")
        return set()

def save_sent_orders(sent_orders: Set[str], file_path: str = "data/sent_orders.json") -> bool:
    """Сохранение ID отправленных заказов в файл"""
    try:
        file = Path(file_path)
        
        # Создаем папку, если не существует
        file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {order_id: 1 for order_id in sent_orders}
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return True
        
    except Exception as e:
        logger.error(f"Error saving sent orders: {str(e)}")
        return False