from datetime import datetime, timedelta
import logging
from typing import Any, Optional, Dict  

from src.utils.body_types import BODY_TYPE_TRANSLATION
from src.utils.cities_reference import CITIES_REFERENCE, find_city_in_address
from fuzzywuzzy import fuzz, process

logger = logging.getLogger(__name__)

def get_safe(dictionary: Any, keys: list, default: Any = None) -> Any:
    """Безопасное получение значения из вложенных словарей"""
    if not isinstance(dictionary, dict):
        return default
        
    current = dictionary
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current

def format_timedelta(delta: timedelta) -> str:
    """Форматирование временного интервала в читаемый вид"""
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} д. {hours} ч. {minutes} мин."
    elif hours > 0:
        return f"{hours} ч. {minutes} мин."
    else:
        return f"{minutes} мин."

def format_datetime(datetime_str: Optional[str]) -> str:
    """Форматирование даты в понятный формат"""
    try:
        if not datetime_str or datetime_str == "N/A":
            return "не указана"
            
        dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception as e:
        logger.error(f"Error formatting datetime: {str(e)}")
        return "неизвестно"

def extract_city_from_address(address: Optional[str]) -> Optional[str]:
    """Извлечение названия города из адреса"""
    if not address or not isinstance(address, str):
        return None
    
    parts = [part.strip() for part in address.split(",")]
    if parts:
        city_part = parts[0].split(" ")[0]
        return city_part
    
    return None

def fuzzy_find_city(address: Optional[str]) -> Optional[str]:
    """Нечеткий поиск города в адресе"""
    if not address or not isinstance(address, str):
        return None
    
    address_clean = address.lower().replace("г.", "").replace("город", "").strip()
    cities = list(CITIES_REFERENCE.keys())
    result = process.extractOne(address_clean, cities, scorer=fuzz.token_set_ratio)
    
    if result and result[1] > 70:
        return CITIES_REFERENCE[result[0]]
    
    return None

def format_datetime_with_timezone(datetime_str: Optional[str]) -> str:
    """Форматирование даты с учетом часового пояса"""
    try:
        if not datetime_str or datetime_str == "N/A":
            return "не указана"
            
        dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception as e:
        logger.error(f"Error formatting datetime with timezone: {str(e)}")
        return "неизвестно"

def get_timezone_from_datetime(datetime_str: Optional[str]) -> str:
    """Извлечение часового пояса из строки даты"""
    try:
        if not datetime_str or datetime_str == "N/A":
            return "часовой пояс не указан"
            
        if "Z" in datetime_str:
            return "UTC"
            
        if "+" in datetime_str:
            tz_part = datetime_str.split("+")[1]
            if ":" in tz_part:
                return f"UTC+{tz_part.split(':')[0]}"
            return f"UTC+{tz_part[:2]}"
            
        if "-" in datetime_str:
            tz_part = datetime_str.split("-")[1]
            if ":" in tz_part:
                return f"UTC-{tz_part.split(':')[0]}"
            return f"UTC-{tz_part[:2]}"
            
        return "часовой пояс не указан"
    except Exception as e:
        logger.error(f"Error determining timezone: {str(e)}")
        return "часовой пояс не указан"

def translate_body_types(body_types: list) -> str:
    """Перевод типов кузова на русский язык"""
    if not body_types:
        return "не указаны"
    
    translated = [BODY_TYPE_TRANSLATION.get(bt, bt) for bt in body_types]
    return ", ".join(translated) if translated else "не указаны"

def format_order_message(order: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Форматирование сообщения о заказе с нечетким поиском городов"""
    try:
        if not isinstance(order, dict):
            raise ValueError("Invalid order format")

        # Основная информация
        order_id = get_safe(order, ["id"], "неизвестен")
        customer = get_safe(order, ["customer", "customerName"], "неизвестен")
        time_left = get_safe(order, ["auction", "timeLeft"], "не указано")
        
        # Даты создания и обновления заказа
        created_at = format_datetime(get_safe(order, ["createdAt", "time"]))
        updated_at = format_datetime(get_safe(order, ["updatedAt", "time"]))
        
        # Характеристики груза
        weight = get_safe(order, ["dimensions", "weight"], "не указан")
        volume = get_safe(order, ["dimensions", "volume"], "не указан")
        
        # Перевод типов кузова
        body_types = translate_body_types(get_safe(order, ["bodyType"], []))
        
        # Информация о торгах
        currency = get_safe(order, ["auction", "currency"], "не указана")
        amount = get_safe(order, ["distribution", "amount"], "не указана")

        # Обработка маршрутов
        shipments = get_safe(order, ["shipments"], [])
        route_points = []
        loading_info = None
        unloading_infos = []

        if shipments:
            for shipment in shipments:
                # Обработка погрузки
                loading_address = get_safe(shipment, ["npShipment", "npGeoAddress", "address"])
                loading_city = fuzzy_find_city(loading_address) or extract_city_from_address(loading_address)
                loading_date = format_datetime_with_timezone(
                    get_safe(shipment, ["npShipment", "period", "from", "time"]))
                loading_tz = get_timezone_from_datetime(
                    get_safe(shipment, ["npShipment", "period", "from", "time"]))
                
                # Обработка выгрузки
                unloading_address = get_safe(shipment, ["npUnshipment", "npGeoAddress", "address"])
                unloading_city = fuzzy_find_city(unloading_address) or extract_city_from_address(unloading_address)
                unloading_date = format_datetime_with_timezone(
                    get_safe(shipment, ["npUnshipment", "period", "from", "time"]))
                unloading_tz = get_timezone_from_datetime(
                    get_safe(shipment, ["npUnshipment", "period", "from", "time"]))
                
                # Добавляем точки маршрута
                if loading_city and loading_city not in route_points:
                    route_points.append(loading_city)
                    loading_info = {
                        "city": loading_city,
                        "date": loading_date,
                        "timezone": loading_tz
                    }
                
                if unloading_city and unloading_city not in route_points:
                    route_points.append(unloading_city)
                    unloading_infos.append({
                        "city": unloading_city,
                        "date": unloading_date,
                        "timezone": unloading_tz
                    })

        # Формирование строки маршрута
        route_str = " - ".join(route_points) if route_points else "не удалось определить"

        # Формирование сообщения
        message_lines = [
            "🚛 Новый заказ в открытых торгах",
            "",
            f"▪️ Заказчик: {customer}",
            f"▪️ До окончания торгов: {time_left}",
            f"▪️ Заявленная стоимость (без НДС): {amount} {currency}",
            "",
            "📦 Требования к перевозке",
            f"▫️ Грузоподъёмность: {weight} кг",
            f"▫️ Объем: {volume} м³",
            f"▫️ Тип кузова: {body_types}",
            "",
            f"📍 Маршрут: {route_str}"
        ]

        if loading_info:
            message_lines.append(
                f"▫️ Погрузка в {loading_info['city']}: "
                f"{loading_info['date']} ({loading_info['timezone']})"
            )

        for unloading_info in unloading_infos:
            message_lines.append(
                f"▫️ Выгрузка в {unloading_info['city']}: "
                f"{unloading_info['date']} ({unloading_info['timezone']})"
            )

        return {
            "text": "\n".join(message_lines),
            "order_id": order_id
        }

    except Exception as e:
        logger.error(f"Error formatting order: {str(e)}")
        return None