import time
import logging
import traceback
from typing import Dict, Any, Optional

from src.config.settings import get_config, init_config  # ← ИЗМЕНИТЕ ЗДЕСЬ
from src.services.api_client import APIClient
from src.services.telegram_service import TelegramService
from src.utils.file_manager import load_sent_orders, save_sent_orders
from src.utils.formatters import get_safe, format_order_message

logger = logging.getLogger(__name__)

class MagistraliMonitor:
    """Основной класс для мониторинга заказов"""
    
    def __init__(self):
        # Инициализация конфигурации
        self.config = init_config()  # Сохраняем конфиг в переменную
        
        # Инициализация сервисов
        self.api_client = APIClient(self.config["STATIC_TOKEN"])
        self.telegram_service = TelegramService()
        
        # Загрузка отправленных заказов
        self.sent_orders = load_sent_orders()
        logger.info(f"Loaded {len(self.sent_orders)} sent orders")
    
    def process_orders(self) -> None:
        """Обработка заказов"""
        try:
            orders = self.api_client.get_active_orders()
            new_count = 0
            skipped_count = 0
            skipped_reasons = {
                'already_sent': 0,
                'not_active': 0,
                'invalid_data': 0
            }
            
            logger.info(f"Starting processing of {len(orders)} orders")
            
            for order in orders:
                order_id = get_safe(order, ["id"])
                if not order_id:
                    logger.debug(f"Skipped order without ID: {order}")
                    skipped_count += 1
                    skipped_reasons['invalid_data'] += 1
                    continue
                    
                # Проверка на уже отправленные заказы
                if order_id in self.sent_orders:
                    logger.debug(f"Order {order_id} already sent")
                    skipped_count += 1
                    skipped_reasons['already_sent'] += 1
                    continue
                    
                # Проверка активности торгов
                if not self.api_client.is_active_auction(order):
                    logger.debug(f"Order {order_id} skipped - auction not active")
                    skipped_count += 1
                    skipped_reasons['not_active'] += 1
                    continue
                    
                # Форматирование и отправка сообщения
                message_data = format_order_message(order)
                if not message_data:
                    logger.warning(f"Failed to format message for order {order_id}")
                    skipped_count += 1
                    skipped_reasons['invalid_data'] += 1
                    continue
                    
                if self.telegram_service.send_message(message_data):
                    self.sent_orders.add(order_id)
                    new_count += 1
                    logger.info(f"Successfully sent order {order_id}")
                else:
                    logger.warning(f"Failed to send order {order_id}")
                    skipped_count += 1
                    skipped_reasons['invalid_data'] += 1
            
            # Логируем статистику обработки
            logger.info(
                f"Processing completed. "
                f"Total: {len(orders)}, "
                f"New: {new_count}, "
                f"Skipped: {skipped_count} "
                f"(reasons: {skipped_reasons})"
            )
            
            # Сохраняем отправленные заказы
            save_sent_orders(self.sent_orders)
            
        except Exception as e:
            logger.error(f"Error in order processing: {str(e)}\n{traceback.format_exc()}")
    
    def run_monitoring(self) -> None:
        """Основной цикл мониторинга"""
        logger.info("Starting monitoring of active auctions")
        
        if not self.api_client.verify_token():
            logger.error("Invalid token, check settings")
            return
        self.telegram_service.send_startup_message()

        while True:
            try:
                self.process_orders()
                time.sleep(self.config["POLLING_INTERVAL"])
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}\n{traceback.format_exc()}")
                time.sleep(60)