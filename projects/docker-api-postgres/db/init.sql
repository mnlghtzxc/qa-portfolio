-- init.sql — скрипт инициализации базы данных PostgreSQL при первом запуске контейнера
-- Автоматически выполняется сервером PostgreSQL, потому что файл монтируется
-- в директорию /docker-entrypoint-initdb.d/ внутри контейнера db

-- Создаём таблицу products, если она ещё не существует (IF NOT EXISTS)
CREATE TABLE IF NOT EXISTS products (
    -- id — первичный ключ, SERIAL автоматически генерирует уникальное целое число для каждой новой записи
    id SERIAL PRIMARY KEY,
    -- name — название товара, строка длиной до 100 символов, обязательное поле
    name VARCHAR(100),
    -- price — цена товара, NUMERIC(10,2) позволяет хранить числа с двумя знаками после запятой
    price NUMERIC(10,2)
);

-- Наполняем таблицу начальными данными
-- INSERT INTO — добавляем новые строки в таблицу products
INSERT INTO products (name, price) VALUES
('Widget', 9.99),    -- Товар 1: название 'Widget', цена 9.99
('Gadget', 19.99),   -- Товар 2: название 'Gadget', цена 19.99
('Doohickey', 4.49); -- Товар 3: название 'Doohickey', цена 4.49
