FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Настраиваем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем системные зависимости и python пакеты
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Проект работает через main.py (по умолчанию порт берётся из настроек)
EXPOSE 8000

# Запуск
CMD ["python", "main.py"]
