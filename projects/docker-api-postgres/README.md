# Docker для QA: тестовый стенд API + PostgreSQL

## 🎯 Цель
Показать навыки работы с Docker и Docker Compose на уровне Manual QA (API/Backend): разворачивание изолированного тестового стенда из нескольких сервисов, проверка сохранности данных и анализ логов контейнеров. Проект демонстрирует, как тестировщик может быстро развернуть микросервисное окружение, провести smoke-тестирование и исследовать логи.

## 🧠 Ключевые навыки
- Установка Docker Desktop и интеграция с WSL2 (Windows 11)
- Запуск готовых контейнеров с пробросом портов (`-p`) и монтированием томов (`-v`)
- Написание собственного Dockerfile для Python-приложения (Flask)
- Связывание сервисов (API + PostgreSQL) через Docker Compose
- Инициализация базы данных SQL-скриптом при старте контейнера
- Проверка работоспособности API с помощью `curl`
- Просмотр логов контейнеров (`docker logs`, `docker compose logs`)
- Доступ внутрь контейнера (`docker exec -it`)
- Понимание жизненного цикла контейнера, отличий образа от контейнера
- Понимание разницы между PowerShell и WSL, контекст использования

## 🛠️ Инструменты
- **Docker Desktop** (движок + CLI, интеграция с WSL2)
- **Docker Compose v5**
- **Python 3.10-slim** (официальный образ)
- **Flask 3.x**, **psycopg2-binary** (драйвер PostgreSQL)
- **PostgreSQL 15-alpine** (официальный образ)
- **SQL** (DDL + DML для наполнения тестовой базы)

## 📦 Описание тестового стенда

### Структура проекта


### Сервис `db` — PostgreSQL
- Образ: `postgres:15-alpine`
- Переменные окружения:
  - `POSTGRES_USER=qa`
  - `POSTGRES_PASSWORD=qa123`
  - `POSTGRES_DB=products_db`
- Порт `5432` проброшен на хост (можно подключаться любым клиентом)
- При первом запуске автоматически выполняется скрипт `init.sql`, монтированный в `/docker-entrypoint-initdb.d/`, который создаёт таблицу `products` и добавляет три товара

### Сервис `api` — Flask-приложение
- Собирается из `Dockerfile` в папке `app`
- Зависимости: `flask`, `psycopg2-binary`
- Переменные окружения для подключения к БД:
  - `DB_HOST=db` (имя сервиса в сети Compose)
  - `DB_NAME=products_db`
  - `DB_USER=qa`
  - `DB_PASS=qa123`
- Слушает порт `5000`, проброшен на хост как `5000`
- `depends_on: db` — база стартует раньше API
- Реализованы эндпоинты:
  - `GET /products` — возвращает список всех товаров в формате JSON
  - `GET /products/<id>` — возвращает товар по ID или `{"error":"Product not found"}` с кодом 404

### Инициализация БД (`init.sql`)

    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        price NUMERIC(10,2)
    );
    
    INSERT INTO products (name, price) VALUES
    ('Widget', 9.99),
    ('Gadget', 19.99),
    ('Doohickey', 4.49);

## 🧪 Сценарий для QA: как я использую этот стенд в тестировании

1. **Smoke-тест после развёртывания**  
   Запускаю `docker compose up -d` и сразу проверяю основные эндпоинты:
   - `curl http://localhost:5000/products` — ожидаю 3 товара
   - `curl http://localhost:5000/products/2` — получаю конкретный товар
   - `curl http://localhost:5000/products/999` — получаю 404 и JSON с ошибкой

2. **Проверка сохранности данных**  
   Выполняю `docker compose down`, затем `docker compose up -d` — данные остаются на месте, потому что PostgreSQL хранит их в своём томе. Повторяю curl-запросы — товары не пропали.

3. **Анализ логов при баге**  
   Если API ответил неверно, смотрю `docker compose logs` — вижу SQL-запросы, ошибки подключения к БД, traceback Flask.

4. **Прямое подключение к БД**  
   Через DBeaver или `psql` на `localhost:5432` проверяю целостность данных, могу вставить или удалить записи, имитируя граничные случаи.

5. **Воспроизведение инцидента**  
   Разработчик говорит, что на определённой версии образа была проблема — я запускаю контейнер с нужным тегом и воспроизвожу баг локально.

6. **Исследование контейнера**  
   Захожу внутрь API-контейнера через `docker exec -it docker-api-postgres-api-1 sh`, смотрю файлы приложения, проверяю доступность БД по сети (контейнеры видят друг друга по именам сервисов).

## ⚠️ Честное признание (learning in progress)
На момент создания проекта я только начинаю контейнеризацию тестовых окружений.  
Код `app.py` и `init.sql` написан с помощью ИИ-наставника, но **каждая строка Dockerfile и docker-compose.yml разобрана и полностью мной понята**:
- как `FROM`, `COPY`, `RUN`, `CMD` собирают образ,
- как `ports`, `environment`, `volumes`, `depends_on` связывают сервисы,
- как `init.sql` автоматически исполняется при старте PostgreSQL,
- как volume сохраняет данные между перезапусками.  

Этот проект — фиксация моей текущей точки роста: я умею поднимать микросервисное окружение одной командой, тестировать API и проверять логи, а написание кастомных образов осваиваю осознанно, с пониманием каждого шага.

## 📂 Структура проекта
- [`app/app.py`](./app/app.py) — исходный код Flask-приложения
- [`app/requirements.txt`](./app/requirements.txt) — зависимости Python
- [`app/Dockerfile`](./app/Dockerfile) — инструкция сборки образа API
- [`db/init.sql`](./db/init.sql) — SQL-скрипт инициализации
- [`docker-compose.yml`](./docker-compose.yml) — описание сервисов

## 🖼️ Доказательства работы

1. **Запуск контейнеров и статус сервисов**  

       $ docker compose up -d
       $ docker compose ps
       NAME                        IMAGE                     STATUS          PORTS
       docker-api-postgres-api-1   docker-api-postgres-api   Up              0.0.0.0:5000->5000/tcp
       docker-api-postgres-db-1    postgres:15-alpine        Up              0.0.0.0:5432->5432/tcp

2. **Smoke-проверка API**  

       $ curl http://localhost:5000/products
       [{"id":1,"name":"Widget","price":9.99},{"id":2,"name":"Gadget","price":19.99},{"id":3,"name":"Doohickey","price":4.49}]
       
       $ curl http://localhost:5000/products/2
       {"id":2,"name":"Gadget","price":19.99}
       
       $ curl http://localhost:5000/products/999
       {"error":"Product not found"}

3. **Данные пережили перезапуск**  

       $ docker compose down
       $ docker compose up -d
       $ curl http://localhost:5000/products
       [{"id":1,"name":"Widget","price":9.99},{"id":2,"name":"Gadget","price":19.99},{"id":3,"name":"Doohickey","price":4.49}]

4. **Логи инициализации БД**  

       db-1  | CREATE TABLE
       db-1  | INSERT 0 3
       db-1  | PostgreSQL init process complete; ready for start up.

5. **Доступ внутрь контейнера API**  

       $ docker exec -it docker-api-postgres-api-1 sh
       # ls /app
       app.py  requirements.txt

## 📌 Как повторить
1. Установить Docker Desktop с WSL2 (Windows) или Docker Engine (Linux/Mac).
2. Склонировать репозиторий и перейти в папку `docker-api-postgres`.
3. Выполнить `docker compose up -d`.
4. Проверить API: `curl http://localhost:5000/products`.
5. Остановить: `docker compose down`.
