#!/bin/bash

# Скрипт для инициализации БД и запуска миграций/сида внутри Docker
# Ожидаем пока Postgres станет доступен

echo "Waiting for PostgreSQL to start..."

# Используем pg_isready для проверки доступности БД
until docker exec genaivideo_db pg_isready -U postgres; do
  sleep 1
done

echo "PostgreSQL is ready!"

echo "Running migrations..."
docker exec genaivideo_bot_api alembic upgrade head

echo "Seeding database..."
docker exec genaivideo_bot_api python seed.py

echo "Done! All systems go."
