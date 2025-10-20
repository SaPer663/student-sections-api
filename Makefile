.PHONY: help build up down restart logs shell db-shell migrate-create migrate-up migrate-down migrate-history test clean prune install dev prod stop ps

# Цвета для вывода
BLUE=\033[0;34m
GREEN=\033[0;32m
RED=\033[0;31m
NC=\033[0m # No Color

# Переменные
DOCKER_COMPOSE=docker-compose
APP_CONTAINER=student_sections_app
DB_CONTAINER=student_sections_db
PYTHON=python3.13


build: ## Собрать Docker образы
	@echo "${BLUE}Сборка Docker образов...${NC}"
	$(DOCKER_COMPOSE) build --no-cache

up: ## Запустить все контейнеры
	@echo "${BLUE}Запуск контейнеров...${NC}"
	$(DOCKER_COMPOSE) up -d
	@echo "${GREEN}Контейнеры запущены!${NC}"
	@echo "API доступен на: http://localhost:8070"
	@echo "Swagger UI: http://localhost:8070/docs"

restart-full: ## Перезапустить контейнеры
	@echo "${BLUE}Перезапуск контейнеров...${NC}"
	$(DOCKER_COMPOSE) down -v && \
	$(DOCKER_COMPOSE) build --no-cache && \
	$(DOCKER_COMPOSE) up -d && \
	$(DOCKER_COMPOSE) logs -f

restart: ## Перезапустить контейнеры
	@echo "${BLUE}Перезапуск контейнеров...${NC}"
	$(DOCKER_COMPOSE) down && \
	$(DOCKER_COMPOSE) build --no-cache && \
	$(DOCKER_COMPOSE) up -d && \
	$(DOCKER_COMPOSE) logs -f

ps: ## Показать статус контейнеров
	@$(DOCKER_COMPOSE) ps

logs: ## Показать логи всех контейнеров
	$(DOCKER_COMPOSE) logs -f


# ============================================
# Качество кода
# ============================================

lint: ## Проверить код с помощью ruff
	@echo "${BLUE}Проверка кода с ruff...${NC}"
	uv run ruff check app/

format: ## Форматировать код с помощью black
	@echo "${BLUE}Форматирование кода с black...${NC}"
	uv run black app/

isort-format: ## Форматировать код с помощью isort
	@echo "${BLUE}Форматирование кода с isort...${NC}"
	uv run isort app/

format-check: ## Проверить форматирование без изменений
	@echo "${BLUE}Проверка форматирования...${NC}"
	uv run black --check app/

mypy: ## Проверить типизацию с помощью mypy
	@echo "${BLUE}Проверка типизации с mypy...${NC}"
	uv run mypy app/

code-quality: format lint mypy ## Запустить все проверки качества кода
	@echo "${GREEN}Все проверки качества кода выполнены!${NC}"


# ============================================
# Управление pgAdmin
# ============================================

pgadmin-up: ## Запустить pgAdmin
	@echo "${BLUE}Запуск pgAdmin...${NC}"
	$(DOCKER_COMPOSE) --profile tools up -d pgadmin
	@echo "${GREEN}pgAdmin доступен на: http://localhost:5050${NC}"
	@echo "Email: admin@admin.com"
	@echo "Password: admin123"

pgadmin-down: ## Остановить pgAdmin
	@echo "${BLUE}Остановка pgAdmin...${NC}"
	$(DOCKER_COMPOSE) --profile tools stop pgadmin
