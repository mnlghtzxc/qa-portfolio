-- Родительские таблицы

-- 1. Кинозалы (Родительская таблица)
CREATE TABLE halls (
   id SERIAL PRIMARY KEY,   -- Автосчетчик ID, Главный ключ
   name TEXT NOT NULL,   -- Название зала, не может быть пустым
   capacity INT NOT NULL CHECK (capacity > 0),   -- Вместимость, не может быть пустым и строго > 0
   base_price DECIMAL (8, 2) NOT NULL CHECK (base_price > 0.00)   -- Базовая цена зала
);

-- 2. Фильмы (Родительская таблица)
CREATE TABLE movies (
   id SERIAL PRIMARY KEY,   -- Уникальный ID фильма, главный ключ
   title TEXT NOT NULL,   -- Название фильма, обязательно
   duration_minutes INT NOT NULL CHECK (duration_minutes > 0), -- длительность в минутах, не может быть пустым и строго > 0
   genre TEXT NOT NULL   -- Жанр фильма, обязательно
);

-- 3. Зарегистрированные юзеры (Родительская таблица)
CREATE TABLE users (
   id SERIAL PRIMARY KEY,   -- ID аккаунта, главный ключ
   name TEXT NOT NULL,   -- имя пользователя, не пустое
   email TEXT NOT NULL UNIQUE   -- email, не пустой + уникальный
);

-- Дочерние таблицы

-- 4. Покупатели (Дочерняя таблица) - Для зарегистрированных юзеров, а также для анонимов
CREATE TABLE customers (
   id SERIAL PRIMARY KEY,   -- уникальный ID покупателя, главный ключ
   user_id INT NULL REFERENCES users(id),   -- если покупка анонимная - NULL, если нет - user(id), внешний ключ
   email TEXT NOT NULL   -- email покупателя (аноним или зарегистрированный)
);

CREATE UNIQUE INDEX registered_customer_email ON customers (email) WHERE user_id IS NOT NULL;   -- Уникальность email только для зарегистрированных

-- 5. Сеансы кинотеатра (Дочерняя таблица)
CREATE TABLE sessions (
   id SERIAL PRIMARY KEY,   -- ID сеанса, главный ключ
   movie_id INT NOT NULL REFERENCES movies(id),   -- какой фильм показываем, внешний ключ
   hall_id INT NOT NULL REFERENCES halls(id),   -- в каком зале показываем, внешний ключ
   start_time TIMESTAMP NOT NULL,   -- дата и время начала сеанса
   end_time TIMESTAMP NOT NULL,   -- дата и время окончания сеанса
   CONSTRAINT check_session_time CHECK (end_time > start_time)   -- проверка сеанса, не может закончиться раньше, чем начался
);

-- 6. Билеты (Дочерняя таблица)
CREATE TABLE tickets (
   id SERIAL PRIMARY KEY,   -- id билета, главный ключ
   session_id INT NOT NULL REFERENCES sessions(id),   -- на какой сеанс куплен билет, внешний ключ
   customer_id INT NOT NULL REFERENCES customers(id),   -- кто купил билет, внешний ключ
   price DECIMAL(8, 2) NOT NULL CHECK (price > 0.00), -- точная цена билета с 2 знаками после запятой
   status TEXT NOT NULL CHECK (status IN ('purchased', 'refund', 'used')),   -- состояние билета, 3 статуса
   created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP   -- время покупки билета
);
