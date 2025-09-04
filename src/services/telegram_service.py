import asyncio
import logging
from typing import Dict, Optional

import backoff
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

from src.config.settings import get_config

logger = logging.getLogger(__name__)

class TelegramService:
    """Сервис для работы с Telegram"""
    
    def __init__(self, bot_token: str = None, channel_id: str = None):
        config = get_config()
        self.bot = Bot(token=bot_token or config["TELEGRAM_BOT_TOKEN"])
        self.channel_id = channel_id or config["TELEGRAM_CHANNEL_ID"]
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    @backoff.on_exception(backoff.expo, 
                         (TelegramError, asyncio.TimeoutError), 
                         max_tries=3)
    async def _send_telegram_async(self, message_data: Dict) -> bool:
        """Асинхронная отправка сообщения с повторными попытками"""
        if not message_data or "text" not in message_data:
            return False
        
        max_retries = 3

        for attempt in range(max_retries):
            try:
                keyboard = [[InlineKeyboardButton("📋 Открыть заказ", 
                            url=f"https://yamagistrali.ru/orders/{message_data['order_id']}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await asyncio.wait_for(
                    self.bot.send_message(
                        chat_id=self.channel_id,
                        text=message_data["text"],
                        disable_web_page_preview=True,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    ),
                    timeout=30.0
                )
                return True
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Timeout sending (attempt {attempt + 1}), waiting {wait_time} sec...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to send order {message_data.get('order_id', 'unknown')} after {max_retries} attempts")
                    return False
            except TelegramError as e:
                logger.error(f"Telegram error: {str(e)}")
                return False
    
    def send_message(self, message_data: Dict) -> bool:
        """Синхронная обертка для отправки в Telegram"""
        try:
            return self.loop.run_until_complete(self._send_telegram_async(message_data))
        except Exception as e:
            logger.error(f"Error sending: {str(e)}")
            return False
    
    def send_startup_message(self) -> bool:
        """Отправка сообщения о запуске бота"""
        startup_message = {
            "text": "🟢 *Бот запущен и начал мониторинг активных торгов*",
            "order_id": "none"
        }
        return self.send_message(startup_message)