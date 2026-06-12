-- Cinema Ticket Purchase API

-- SQL-проверки целостности данных (Manual QA Checks)

-- Этот файл содержит набор запросов, которые помогают убедиться, 
-- что в базе данных нет нарушений бизнес-правил и аномалий.
-- Все запросы должны возвращать 0 строк. Если какой-то запрос
-- возвращает строки — это индикатор проблемы, требующей расследования.

-- 1. Проверка на перепродажу билетов (Overselling)
-- Продано больше билетов, чем вместимость зала
SELECT
    s.id AS session_id,
    h.capacity,
    COUNT(t.id) AS tickets_sold,
    h.capacity - COUNT(t.id) AS free_seats
FROM sessions s
JOIN halls h ON s.hall_id = h.id
LEFT JOIN tickets t ON s.id = t.session_id
    AND t.status IN ('purchased', 'used')
GROUP BY s.id, h.capacity
HAVING COUNT(t.id) > h.capacity;

-- 2. Проверка: использованные билеты только на прошедших сеансах
-- Билет со статусом 'used' не может быть на будущем сеансе
SELECT *
FROM tickets
JOIN sessions ON tickets.session_id = sessions.id
WHERE tickets.status = 'used'
  AND sessions.start_time > NOW();

-- 3. Проверка: купленные билеты только на будущих (или текущих) сеансах
-- Билет со статусом 'purchased' не может быть на уже завершившемся сеансе
SELECT *
FROM tickets
JOIN sessions ON tickets.session_id = sessions.id
WHERE tickets.status = 'purchased'
  AND sessions.end_time < NOW();

-- 4. Уникальность email зарегистрированных пользователей
SELECT email, COUNT(*)
FROM users
GROUP BY email
HAVING COUNT(*) > 1;

-- 5. Уникальность email среди зарегистрированных покупателей
-- Частичный уникальный индекс гарантирует это только для user_id IS NOT NULL
SELECT email, COUNT(*)
FROM customers
WHERE user_id IS NOT NULL
GROUP BY email
HAVING COUNT(*) > 1;

-- 6. Соответствие длительности сеанса и продолжительности фильма
SELECT *
FROM sessions
JOIN movies ON sessions.movie_id = movies.id
WHERE EXTRACT(EPOCH FROM (sessions.end_time - sessions.start_time)) / 60 != movies.duration_minutes;

-- 7. Орфанные билеты: билет без существующего сеанса
SELECT tickets.*
FROM tickets
LEFT JOIN sessions ON tickets.session_id = sessions.id
WHERE sessions.id IS NULL;

-- 8. Орфанные билеты: билет без существующего покупателя
SELECT tickets.*
FROM tickets
LEFT JOIN customers ON tickets.customer_id = customers.id
WHERE customers.id IS NULL;

-- 9. Пересекающиеся сеансы в одном зале
SELECT
    a.id AS session_a,
    b.id AS session_b,
    a.hall_id,
    a.start_time AS a_start,
    a.end_time AS a_end,
    b.start_time AS b_start,
    b.end_time AS b_end
FROM sessions a
JOIN sessions b ON a.hall_id = b.hall_id
WHERE a.id < b.id
  AND a.start_time < b.end_time
  AND a.end_time > b.start_time;

-- 10. Проверка отрицательных или нулевых цен билетов
SELECT *
FROM tickets
WHERE price <= 0;

-- 11. Проверка вместимости залов (неотрицательная)
SELECT *
FROM halls
WHERE capacity <= 0;
