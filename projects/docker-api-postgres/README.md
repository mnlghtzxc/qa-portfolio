# Docker для QA: тестовый стенд API + PostgreSQL

## 🎯 Цель
Показать умение разворачивать изолированное тестовое окружение с помощью Docker и Docker Compose, проверять работу связки «бэкенд — база данных» и анализировать логи контейнеров. Проект имитирует реальный микросервисный стенд, который можно использовать для smoke-тестирования и воспроизведения багов.

## 🧠 Ключевые навыки
- Установка и настройка Docker Desktop на Windows 11 (WSL2)
- Запуск готовых контейнеров с пробросом портов и томов
- Написание собственного Dockerfile для Python-приложения на Flask
- Монтирование volume для сохранения данных между перезапусками
- Связывание нескольких сервисов через `docker-compose.yml`
- Инициализация PostgreSQL скриптом (`init.sql`)
- Проверка работоспособности API с помощью `curl`
- Анализ логов контейнеров (`docker logs`, `docker compose logs`)
- Доступ внутрь контейнера (`docker exec -it ... sh`)
- Понимание разницы между образами и контейнерами, портами хоста и контейнера

## 🛠️ Инструменты
- Docker Desktop (движок + CLI)
- Docker Compose v5
- Python 3.10 (официальный slim-образ)
- Flask 3.x
- Psycopg2 (драйвер PostgreSQL)
- PostgreSQL 15 (Alpine-образ)
- SQL (DDL + DML для наполнения тестовыми данными)

## 📦 Описание тестового стенда

### Структура проекта


### Сервис `db` (PostgreSQL)
- Официальный образ `postgres:15-alpine` (легковесный)
- Переменные окружения: `POSTGRES_USER=qa`, `POSTGRES_PASSWORD=qa123`, `POSTGRES_DB=products_db`
- Порт `5432` проброшен на хост для возможности прямого подключения (например, из DBeaver)
- Volume: файл `init.sql` монтируется в `/docker-entrypoint-initdb.d/` — скрипт выполняется автоматически при первом запуске контейнера, создавая таблицу `products` и добавляя три товара

### Сервис `api` (Flask)
- Собирается из Dockerfile в папке `app`
- Зависимости: `flask`, `psycopg2-binary`
- Принимает переменные окружения: `DB_HOST=db`, `DB_NAME=products_db`, `DB_USER=qa`, `DB_PASS=qa123`
- Слушает порт `5000`, который проброшен на хост как `5000`
- `depends_on: db` гарантирует, что база стартует первой
- Реализованы два эндпоинта:
  - `GET /products` — возвращает все товары
  - `GET /products/<id>` — возвращает товар по ID или ошибку 404

### Инициализация БД (`init.sql`)
```sql
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price NUMERIC(10,2)
);

INSERT INTO products (name, price) VALUES
('Widget', 9.99),
('Gadget', 19.99),
('Doohickey', 4.49);
