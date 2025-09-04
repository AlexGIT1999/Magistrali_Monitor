FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости сначала для кэширования
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src/ src/
COPY config.json.example config.json
COPY .gitignore .
COPY README.md .

# Создаем папку для данных
RUN mkdir -p data

# Запускаем приложение
CMD ["python", "src/main.py"]