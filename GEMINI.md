# GEMINI.md — Проектная документация

## Суть проекта

Telegram-бот для **продажи AI-сгенерированных видео** по загруженному пользователем фото.
Пользователь выбирает шаблон → загружает фото → (опц.) пишет пожелания → бот ставит задачу в очередь → результат отправляется в чат.

Монетизация через **наборы (паки) генераций** — пользователь покупает пак из N генераций (включая единоразовые).

Проект состоит из **Telegram-бота** и встроенного **FastAPI-сервера**, которые запускаются в одном процессе (в одном asyncio event loop), разделяя общую базу данных и бизнес-логику. FastAPI в будущем будет обслуживать запросы независимой веб-админки.

---

## Стек технологий

| Слой | Технология |
|---|---|
| Фреймворк бота | **aiogram 3.x** (async, polling) |
| API / Админка | **FastAPI** (uvicorn) |
| ORM / БД | **SQLAlchemy 2.x** (async), **PostgreSQL**, **Alembic** |
| Конфигурация | **pydantic-settings** (`.env`) |
| Логирование | `logging` + `RotatingFileHandler` |
| Генерация видео | Абстрактный `BaseGenerator` + мок-реализации |

---

## Бизнес-логика (текущее состояние)

- **Бот полностью написан**: роутеры, сервисы, репозитории, клавиатуры, мидлвари работают.
- **Реферальная система**: реализована в `UserMiddleware`, работает атомарно при регистрации, выдает 1 генерацию за приглашение.
- **Оплата**: мок-оплата с зачислением баланса.
- **Генерация видео**: работает через `MockGenerator` (возвращает тестовое видео через 5 секунд).
- **База данных**: настроена, все таблицы (`User`, `Template`, `Pack`, `Generation` и др.) созданы, настроено каскадное удаление.

---

## Архитектурные паттерны

### Единый процесс для Бота и API (FastAPI Lifespan)
Бот и FastAPI работают вместе. FastAPI является основным приложением, которое запускается через `uvicorn`. 
Бот стартует в фоне (через `asyncio.create_task`) внутри FastAPI `lifespan` контекста. Это позволяет:
- Использовать один `SQLAlchemyUnitOfWork`.
- Использовать одни и те же сервисы из `services/`.
- Вызывать методы айОграма вроде `bot.send_message()` прямо из FastAPI-эндпоинтов веб-админки.

### Unit of Work (UoW)
`SQLAlchemyUnitOfWork` — асинхронный контекстный менеджер для транзакций БД.

### Сервисный слой
Роутеры Telegram и эндпоинты FastAPI — **тонкие**. Вся логика находится в `services/` (`UserService`, `PackService`, `GenerationService`, `TemplateService`), которые получают UoW через аргументы или зависимости.

---

## Структура проекта

```
genaivideobot/
├── main.py                         # Старт uvicorn сервера
├── bootstrap.py                    # Инициализация бота (bot_manager, dp_manager)
│
├── config/
│   ├── settings.py                 # Config(BaseSettings)
│   └── logging_setup.py            # setup_logging()
│
├── presentation/                   # FastAPI-часть
│   ├── bootstrap.py                # Создание FastAPI (create_app), lifespan, CORS
│   ├── dependencies.py             # FastAPI Depends (get_uow_dependency)
│   └── api/v1/
│       └── routers/                # Эндпоинты API админки
│
├── db/
│   ├── session.py                  # async_sessionmaker
│   ├── uow.py                      # SQLAlchemyUnitOfWork + все репозитории
│   ├── models/                     # SQLAlchemy Declartive Base модели
│   └── repo/                       # CRUD для БД
│
├── bot/                            # Aiogram-часть
│   ├── builder/                    # Инициализация бота
│   ├── routers/                    # Клиентские роутеры (start, pack, template...)
│   ├── middlewares/                # UoWMiddleware, UserMiddleware, UserActionMiddleware
│   ├── keyboards/                  # Кнопки
│   ├── locales/                    # ru.py, en.py (тексты)
│   └── states/                     # FSM
│
└── services/                       # Бизнес-логика (User, Pack, Gen, Template)
    └── providers/
        └── ai_video_generators/    # BaseGenerator, MockGenerator
```

---

## Команды

```bash
# Запуск бота и API
python main.py

# Миграции (Alembic)
cd db && alembic upgrade head
cd db && alembic revision --autogenerate -m "описание"

```bash
# Заполнение тестовыми данными (шаблоны, паки)
python seed.py
```

---

## PiAPI Integration

### Documentation
- [Overview](https://piapi.ai/docs/overview.md) - Intro to Midjourney, Flux, Kling, Hailuo, etc.
- [Quick Start](https://piapi.ai/docs/quickstart.md) - API Key and Base URL setup.
- [File Upload API](https://piapi.ai/docs/tools/file-upload.md) - Ephemeral storage for image/video inputs.
- [Hailuo API](https://piapi.ai/docs/hailuo-api/generate-video.md) - Video generation with MiniMax model.
- [Unified API Schema](https://piapi.ai/docs/unified-api-schema.md) - Standardized endpoints for all models.

### Endpoints
- **Base URL**: `https://api.piapi.ai/api/v1/task`
- **Upload URL**: `https://upload.theapi.app/api/ephemeral_resource`
- **Model (Hailuo 2.3)**: `{"model": "hailuo", "input": {"model": "v2.3-fast"}}`
