import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.config.settings import get_config
from src.utils.formatters import get_safe

logger = logging.getLogger(__name__)

class APIClient:
    """Клиент для работы с API Магистрали"""
    
    def __init__(self, token: str = None, base_url: str = None):
        config = get_config()
        self.token = token or config["STATIC_TOKEN"]
        self.base_url = base_url or config["API_BASE_URL"]
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Создание сессии с настройками"""
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MagistraliMonitor/1.0"
        })
        return session
    
    def verify_token(self) -> bool:
        """Проверка валидности токена"""
        try:
            url = f"{self.base_url}/api/users/userEmployees/get/list/v0"
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return False
    
    def get_active_orders(self) -> List[Dict[str, Any]]:
        """Получение активных заказов"""
        try:
            config = get_config()  # ← ДОБАВЬТЕ ЭТУ СТРОКУ
            lookback_time = datetime.utcnow() - timedelta(hours=config["LOOKBACK_PERIOD_HOURS"])
            logger.info(f"Requesting orders updated after: {lookback_time.isoformat()}")
            
            url = f"{self.base_url}/api/orders/v0/transferOrder/getFlatForExecutor"
            payload = {
                "data": {
                    "limit": 200,
                    "filter": {
                        "statuses": ["onMatch"],
                        "updatedFrom": lookback_time.isoformat() + "Z"
                    }
                }
            }
            
            logger.info(f"Sending request to API: {url}")
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            orders = get_safe(data, ["data", "orders"], [])
            logger.info(f"Received {len(orders)} orders from API")
            
            # Логируем первые 3 заказа для отладки
            for i, order in enumerate(orders[:3]):
                logger.info(f"Example order {i+1}: ID={get_safe(order, ['id'])} "
                          f"Status={get_safe(order, ['status'])} "
                          f"Auction status={get_safe(order, ['matcher', 'matcherStatus'])}")
            
            return [order for order in orders if isinstance(order, dict)]
            
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            return []
    
    def is_active_auction(self, order: Dict[str, Any]) -> bool:
        """Проверка активности торгов с подробным логированием"""
        try:
            if not isinstance(order, dict):
                logger.debug("Skipped order - not a dictionary")
                return False
                
            order_id = get_safe(order, ["id"], "unknown")
            
            # Основные параметры
            status = get_safe(order, ["status"])
            winner = get_safe(order, ["matcher", "winnerExecutor"])
            time_left = self._calculate_time_left(order)
            
            # Подробное логирование
            logger.debug(f"Checking order {order_id}: "
                        f"status={status}, "
                        f"winner={winner is not None}, "
                        f"time_left={time_left}")
            
            # Упрощенные критерии активности
            if winner is not None:
                logger.debug(f"Order {order_id} - has winner")
                return False
                
            if status != "onMatch":
                logger.debug(f"Order {order_id} - invalid status")
                return False
                
            if "завершены" in time_left:
                logger.debug(f"Order {order_id} - auction completed")
                return False
                
            logger.debug(f"Order {order_id} - auction active")
            return True
            
        except Exception as e:
            logger.error(f"Error checking order {order_id}: {str(e)}")
            return False
    
    def _calculate_time_left(self, order: Dict[str, Any]) -> str:
        """Вычисление оставшегося времени до окончания торгов"""
        try:
            # Проверяем наличие победителя
            if get_safe(order, ["matcher", "winnerExecutor"]) is not None:
                return "торги завершены (есть победитель)"
                
            # Проверяем время окончания из matcherAuction (приоритет)
            matcher_end_time_str = get_safe(order, ["matcher", "matcherAuction", "endDate", "time"])
            if matcher_end_time_str and matcher_end_time_str != "N/A":
                matcher_end_time = datetime.fromisoformat(matcher_end_time_str.replace("Z", "+00:00"))
                now = datetime.now(matcher_end_time.tzinfo)
                if now >= matcher_end_time:
                    return "торги завершены"
                delta = matcher_end_time - now
                return self._format_timedelta(delta)
                
            # Проверяем время окончания из auction
            end_time_str = get_safe(order, ["auction", "endDate", "time"])
            if end_time_str and end_time_str != "N/A":
                end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
                now = datetime.now(end_time.tzinfo)
                if now >= end_time:
                    return "торги завершены"
                delta = end_time - now
                return self._format_timedelta(delta)
                
            # Проверяем длительность для типа duration
            duration = get_safe(order, ["auction", "duration"], 0)
            auction_type = get_safe(order, ["auction", "auctionType"], "period")
            if duration and auction_type == "duration":
                start_time_str = get_safe(order, ["auction", "startDate", "time"])
                if start_time_str and start_time_str != "N/A":
                    start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                    end_time = start_time + timedelta(seconds=duration)
                    now = datetime.now(end_time.tzinfo)
                    if now >= end_time:
                        return "торги завершены"
                    delta = end_time - now
                    return self._format_timedelta(delta)
                    
            return "не указано"
        except Exception as e:
            logger.error(f"Error calculating time: {str(e)}")
            return "неизвестно"
    
    def _format_timedelta(self, delta: timedelta) -> str:
        """Форматирование временного интервала (вспомогательный метод)"""
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days} д. {hours} ч. {minutes} мин."
        elif hours > 0:
            return f"{hours} ч. {minutes} мин."
        else:
            return f"{minutes} мин."