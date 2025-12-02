# snip727-v2 — DeFi Sniping Bot

Минималистичный скелет асинхронного бота для снипинга DeFi токенов.

## Стек

- **Python 3.11**
- **Web3.py** — взаимодействие с блокчейном
- **SQLAlchemy** + **asyncpg** — асинхронная работа с БД
- **Alembic** — управление миграциями
- **python-telegram-bot** — Telegram интеграция
- **Redis** — кэширование и очереди
- **structlog** — структурированное логирование
- **Poetry** — управление зависимостями

## Структура проекта

```
snip727-v2/
├── src/snip727/
│   ├── core/           # Конфигурация и утилиты
│   ├── db/             # Слой базы данных
│   ├── bot/            # Telegram бот
│   └── web3/           # Интеграция с блокчейном
├── tests/              # Тесты
├── migrations/         # Alembic миграции
├── docker-compose.yml  # Docker контейнеры
├── pyproject.toml      # Конфигурация Poetry
└── README.md           # Этот файл
```

## Быстрый старт

### 1. Установка зависимостей

```bash
poetry install
```

### 2. Конфигурация

Скопируйте `.env.example` в `.env`:

```bash
cp .env.example .env
```

Отредактируйте `.env` с вашими параметрами:

```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 3. Запуск через Docker Compose

```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL 16
- Redis 7
- Telegram бот

### 4. Запуск локально

Убедитесь, что PostgreSQL и Redis работают:

```bash
# Миграции БД
poetry run alembic upgrade head

# Запуск бота
poetry run bot
```

## Команды бота

- `/start` — информация о боте
- `/status` — статус бота и его компонентов

## Разработка

### Линтинг и проверка типов

```bash
poetry run ruff check .
poetry run mypy src/
```

### Тесты

```bash
poetry run pytest
poetry run pytest --cov
```

### Создание миграции БД

```bash
poetry run alembic revision --autogenerate -m "описание миграции"
```

## Следующие шаги

- [ ] Мониторинг пулов Uniswap
- [ ] Анализ настроения (DeepPavlov)
- [ ] Стратегия N-of-4
- [ ] Интеграция с MEV-protection
- [ ] Метрики и алерты

## Лицензия

MIT
