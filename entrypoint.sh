#!/bin/bash
set -e

# Add current directory to PYTHONPATH for imports to work
export PYTHONPATH=$PYTHONPATH:/app

# Ожидание Postgres
echo "Waiting for PostgreSQL at $DATABASE_HOST:$DATABASE_PORT..."
while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

# Запуск миграций
echo "Running alembic migrations..."
alembic upgrade head

# Заполнение данными (seed)
echo "Running seed script..."
python seed.py

# Запуск основного приложения
echo "Starting application..."
exec python main.py
