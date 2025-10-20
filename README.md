# Student Sections API

REST API для управления студентами и секциями с системой ролей и JWT авторизацией.

## Стек

- Python 3.13
- FastAPI
- SQLAlchemy 2.0 + asyncpg
- PostgreSQL
- Alembic
- JWT (python-jose)
- pytest

## Быстрый старт

Клонируйте репозиторий:
```bash
git clone https://github.com/SaPer663/student-sections-api.git
cd student-sections-api
```

Создайте `.env` файл:
```bash
cp .env.example .env
```

Отредактируйте переменные окружения при необходимости.

Запустите через Docker Compose:
```bash
docker-compose up --build
```

API будет доступен по адресу `http://localhost:8000`

## Первый запуск

После старта контейнеров автоматически:
- Применятся миграции базы данных
- Создадутся роли `admin` и `user`
- Будет создан первый администратор

**Учетные данные администратора:**
- Email: `admin@example.com`
- Пароль: `admin123`

## Загрузка демо-данных

Для тестирования API в окружении `development` загрузятся тестовые данные:

- 7 секций (Python, Math, Physics и т.д.)
- 15 студентов
- ~20 записей в секции

## Документация API

После запуска доступна интерактивная документация:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`


## Пример использования

Получить токен:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

Получить список студентов:
```bash
curl http://localhost:8000/api/v1/students \
  -H "Authorization: Bearer YOUR_TOKEN"
```


## Архитектура

Проект использует слоистую архитектуру:
- **API Layer** - FastAPI endpoints
- **Service Layer** - бизнес-логика
- **Repository Layer** - работа с БД
- **Models** - SQLAlchemy модели

Применены паттерны: Repository, Service Layer, Dependency Injection, DTO (Pydantic).

## Health Check

```bash
curl http://localhost:8000/health
```

## Остановка

```bash
docker-compose down
```

Для удаления данных:
```bash
docker-compose down -v
```
