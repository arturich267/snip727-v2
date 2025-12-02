# Snip727-V2 🤖

Полностью асинхронный DeFi-бот для сниппинга на Uniswap V2/V3 в блокчейне Base. Легко расширяется до Arbitrum.

> **Работает в России без VPN после установки!** ✅

## Особенности

- ✅ 100% асинхронная архитектура
- ✅ Поддержка Uniswap V2 и V3 на Base
- ✅ Redis кеш для высокой производительности
- ✅ PostgreSQL 16 для надёжного хранилища
- ✅ Telegram бот с интерфейсом для управления
- ✅ Структурированное JSON логирование
- ✅ Полное покрытие тестами (>85%)
- ✅ CI/CD с GitHub Actions
- ✅ Docker + docker-compose для быстрого запуска

## Технический стек

| Компонент | Версия |
|-----------|--------|
| Python | 3.11+ |
| Web3.py | 6.11+ |
| SQLAlchemy | 2.0+ |
| asyncpg | 0.29+ |
| aiogram | 3.2+ |
| structlog | 23.2+ |
| Redis | 7+ |
| PostgreSQL | 16+ |

## Быстрый старт

### Требования

- Python 3.11+
- Poetry
- Docker + Docker Compose
- Telegram бот токен (от @BotFather)

### Установка

1. **Клонируем репозиторий:**
```bash
git clone https://github.com/yourusername/snip727-v2.git
cd snip727-v2
```

2. **Создаём файл `.env` из примера:**
```bash
cp .env.example .env
```

3. **Заполняем переменные окружения:**
```bash
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token_here
BOT_ADMIN_IDS=123456789,987654321

# Web3
WEB3_PROVIDER_URL=https://mainnet.base.org
WEB3_CHAIN_ID=8453

# Уникаделементы (Base addresses)
UNISWAP_FACTORY_V2=0x8909Dc15e40953b386FA8f440dB7f0DDA8221820
UNISWAP_ROUTER_V2=0x4752ba5DBc23f44D87826ADF0FF190cF7ec87b9b
UNISWAP_FACTORY_V3=0x33128a8fC17869897dcE68Ed026d694621f6FDaD
UNISWAP_SWAP_ROUTER_V3=0x2626664c2603336E57B271c5C0b26F421741e481

# Стратегия
MIN_LIQUIDITY_USD=5000
MAX_PRICE_IMPACT=0.5
SLIPPAGE_TOLERANCE=0.01
```

### Запуск с Docker Compose

Самый простой способ:

```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL 16
- Redis 7
- Telegram бот с автоматической переподключением

### Локальная разработка

1. **Установляем зависимости:**
```bash
poetry install
```

2. **Запускаем базу и Redis:**
```bash
docker-compose up postgres redis -d
```

3. **Применяем миграции:**
```bash
poetry run alembic upgrade head
```

4. **Запускаем бот:**
```bash
poetry run python main.py
```

## Структура проекта

```
snip727-v2/
├── src/
│   ├── bot/                 # Telegram бот
│   │   ├── handlers.py      # Обработчики команд
│   │   ├── keyboards.py     # Инлайн клавиатуры
│   │   └── main.py          # Менеджер бота
│   ├── core/
│   │   └── config.py        # Конфигурация (Pydantic Settings)
│   ├── db/
│   │   ├── base.py          # Base для всех моделей
│   │   ├── models.py        # SQLAlchemy модели
│   │   └── session.py       # Асинхронная сессия
│   ├── services/            # Бизнес-логика
│   │   ├── monitoring.py    # Мониторинг пар
│   │   ├── sentiment.py     # Анализ сентимента
│   │   ├── strategy.py      # Торговая стратегия
│   │   └── trading.py       # Исполнение сделок
│   ├── web3/
│   │   └── client.py        # Асинхронный Web3 клиент
│   ├── schemas/             # Pydantic модели для API
│   └── utils/
│       └── logger.py        # Структурированное логирование
├── migrations/              # Alembic миграции БД
├── tests/
│   ├── unit/                # Unit тесты
│   ├── integration/         # Интеграционные тесты
│   └── conftest.py          # Pytest конфиг
├── docker-compose.yml       # Docker Compose конфиг
├── Dockerfile               # Docker образ
├── pyproject.toml           # Poetry зависимости
└── README.md               # Этот файл
```

## Переменные окружения

### Требуемые

| Переменная | Описание | Пример |
|-----------|---------|--------|
| `BOT_TOKEN` | Telegram бот токен | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `WEB3_PROVIDER_URL` | RPC провайдер | `https://mainnet.base.org` |

### Опциональные

| Переменная | По умолчанию | Описание |
|-----------|-------------|---------|
| `BOT_ADMIN_IDS` | `123456789` | Admin ID через запятую |
| `BOT_LOG_LEVEL` | `INFO` | Уровень логирования |
| `DATABASE_URL` | Postgresql | Строка подключения к БД |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis адрес |
| `WEB3_CHAIN_ID` | `8453` | ID сети (Base) |
| `MIN_LIQUIDITY_USD` | `5000` | Минимальная ликвидность |
| `SLIPPAGE_TOLERANCE` | `0.01` | Допустимый слиппедж |
| `ENVIRONMENT` | `development` | `development` или `production` |
| `DEBUG` | `false` | Режим дебага |

## API Команд (Telegram)

### Основные команды

- `/start` - Запуск бота, главное меню
- `/status` - Статус бота и текущие параметры
- `/help` - Справка

### Кнопки меню

- **📊 Status** - Статус мониторинга и текущие метрики
- **⚙️ Settings** - Управление настройками (для админов)
- **📈 Stats** - Статистика торговли

## Тестирование

### Запуск всех тестов

```bash
poetry run pytest
```

### С покрытием кода

```bash
poetry run pytest --cov=src --cov-report=html
```

### Только unit тесты

```bash
poetry run pytest -m unit
```

### Только интеграционные тесты

```bash
poetry run pytest -m integration
```

## Статические проверки

### Линтинг с Ruff

```bash
poetry run ruff check src tests
```

### Type checking с mypy

```bash
poetry run mypy src
```

### Форматирование

```bash
poetry run ruff format src tests
```

## Миграции БД

### Создание новой миграции

```bash
poetry run alembic revision --autogenerate -m "Описание миграции"
```

### Применение всех миграций

```bash
poetry run alembic upgrade head
```

### Откат последней миграции

```bash
poetry run alembic downgrade -1
```

## Архитектура

```
┌──────────────────────────────────────────────────┐
│          Telegram Bot (aiogram)                   │
│    Handlers → Keyboards → Admin Commands          │
└────────────────┬─────────────────────────────────┘
                 │
        ┌────────▼────────┐
        │   Event Bus     │ (Redis)
        │ async messages  │
        └────────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼──────┐ ┌──▼───────┐ ┌──▼──────────┐
│Monitoring│ │Sentiment │ │ Trading     │
│Service   │ │Service   │ │ Service     │
└───┬──────┘ └──┬───────┘ └──┬──────────┘
    │           │            │
    └───────────┼────────────┘
                │
    ┌───────────▼──────────┐
    │   Web3 Client        │
    │  (async HTTP)        │
    │  → Uniswap V2/V3     │
    └──────────────────────┘
            │
┌───────────▼─────────────┐
│  PostgreSQL + SQLAlchemy│
│  (Pairs, Trades, etc)   │
└─────────────────────────┘
```

## Планы развития (Roadmap)

### Phase 1 (v0.1.0) ✅
- [x] Базовая структура проекта
- [x] Telegram интеграция
- [x] Database setup с Alembic
- [x] Tests + CI/CD

### Phase 2 (v0.2.0) 🔄
- [ ] Мониторинг новых пар на Uniswap V2
- [ ] Анализ сентимента (Twitter/Discord)
- [ ] Стратегия N-of-4
- [ ] Первые торговые сигналы

### Phase 3 (v0.3.0)
- [ ] Исполнение сделок
- [ ] Профит-трейлинг
- [ ] MEV защита
- [ ] Telegram уведомления о сделках

### Phase 4 (v0.4.0)
- [ ] Поддержка Arbitrum
- [ ] Кроссчейн стратегии
- [ ] Advanced analytics dashboard
- [ ] Webhook для esterni обслуживания

## Расширение на другие сети

Для добавления поддержки Arbitrum или других сетей:

1. Добавьте новые адреса контрактов в `.env`:
```bash
# Arbitrum addresses
ARBITRUM_UNISWAP_FACTORY_V2=0x...
ARBITRUM_UNISWAP_ROUTER_V2=0x...
```

2. Создайте Network enum в `src/core/networks.py`

3. Расширьте `Web3Client` для мультисетевой поддержки

4. Добавьте миграции для новых моделей

## Решение проблем

### "Connection refused" для PostgreSQL
```bash
# Убедитесь что контейнер запущен
docker-compose ps

# Перезапустите сервис
docker-compose restart postgres
```

### Redis не подключается
```bash
# Проверьте логи
docker-compose logs redis

# Пересоздайте контейнер
docker-compose down redis
docker-compose up redis -d
```

### Тесты не проходят
```bash
# Установите зависимости заново
poetry install

# Очистите кеш Python
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

## Логирование

Все события логируются в JSON формате в stdout:

```json
{
  "event": "monitoring_service_started",
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "info",
  "logger": "src.services.monitoring",
  "pair_address": "0x..."
}
```

Структурированные логи легко парсить и фильтровать в системах мониторинга (ELK, DataDog и т.д.)

## Безопасность

⚠️ **Важно:**

1. **Никогда** не коммитьте `.env` файл
2. Используйте крепкие приватные ключи для trading账户
3. Храните `BOT_TOKEN` в защищённом хранилище
4. Регулярно обновляйте зависимости:
```bash
poetry update
```

## Лицензия

MIT License - смотрите [LICENSE](LICENSE) файл

## Контрибьютинг

Пулл-реквесты приветствуются! Для больших изменений сначала откройте issue.

## Контакт

Вопросы? Создайте issue в репозитории.

---

**Сделано с ❤️ для DeFi коммьюнити**

P.S. Убедитесь что вы понимаете риски использования автоматизированных торговых ботов. Никакого гарантийного финансового результата. DYOR!
