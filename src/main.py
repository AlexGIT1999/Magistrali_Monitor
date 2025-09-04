import logging
import sys
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('magistrali_monitor.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Основная функция запуска приложения"""
    try:
        logger.info("Starting Magistrali Monitor application")
        
        # Прямые импорты без префикса src
        from core.monitor import MagistraliMonitor
        
        # Создаем и запускаем монитор
        monitor = MagistraliMonitor()
        monitor.run_monitoring()
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # Добавляем текущую директорию в путь для импортов
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    main()