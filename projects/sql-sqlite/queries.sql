-- ============================================
-- SQL для QA: запросы для проверки целостности и анализа данных
-- СУБД: SQLite
-- ============================================

-- 1. Создание таблицы users
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Начальное наполнение (первые три пользователя)
INSERT INTO users (username, email) VALUES 
('alex_qa', 'alex.qa@example.com'),
('elena_test', 'elena.t@example.com'),
('bug_hunter', 'hunter@example.com');

-- Добавление новых полей: роль и возраст
ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user';
ALTER TABLE users ADD COLUMN age INTEGER;

-- Обновление возраста
UPDATE users SET age = 20 WHERE id = 1;
UPDATE users SET age = 22 WHERE id = 3;

-- Вставка дополнительных пользователей с разными ролями
INSERT INTO users (username, email, role, age) VALUES ('vlad_qa', 'vlad.qa@example.com', 'user', 32);
INSERT INTO users (username, email, role, age) VALUES ('cat_qa', 'cat.qa@example.com', 'user', 7);
INSERT INTO users (username, email, role, age) VALUES ('jack', 'jack@example.com', 'admin', 40);
INSERT INTO users (username, email, role, age) VALUES ('lisa', 'lisa@example.com', 'moderator', 21);

-- Переименование пользователя (alex_qa -> sasha_qa)
UPDATE users SET username = 'sasha_qa' WHERE username = 'alex_qa';

-- 2. Базовые выборки и фильтрация
-- Все пользователи
SELECT * FROM users;

-- Пользователь по username
SELECT * FROM users WHERE username = 'elena_test';

-- Пользователи с email на example.com
SELECT * FROM users WHERE email LIKE '%example.com';

-- Условия AND
SELECT * FROM users WHERE id > 2 AND username LIKE '%hunter%';

-- Зарегистрированные после 2026-01-01
SELECT * FROM users WHERE registered_at > '2026-01-01 00:00:00';

-- 3. Агрегация и группировка
-- Количество по ролям
SELECT role, COUNT(*) FROM users GROUP BY role;

-- Средний возраст по ролям
SELECT role, AVG(age) FROM users GROUP BY role;

-- Роль с максимальным количеством пользователей
SELECT role, COUNT(*) AS cnt FROM users GROUP BY role ORDER BY cnt DESC LIMIT 1;

-- Проверка уникальности email (дубликатов быть не должно)
SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1;

-- Границы id
SELECT MIN(id), MAX(id) FROM users;

-- 4. Таблица posts и внешний ключ
PRAGMA foreign_keys = ON;

CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Посты для пользователей (использую подзапросы для надёжной привязки)
INSERT INTO posts (user_id, title, body) VALUES 
((SELECT id FROM users WHERE username = 'sasha_qa'), 'Nazvanie', 'Soderzhanie'),
((SELECT id FROM users WHERE username = 'bug_hunter'), 'Bolshoi ohotnik', 'Lubit ohotu'),
((SELECT id FROM users WHERE username = 'bug_hunter'), 'Malenkiny ohotnik', 'NE lubit ohotu'),
((SELECT id FROM users WHERE username = 'vlad_qa'), 'Hochu offer', 'gotov vkalivat'),
((SELECT id FROM users WHERE username = 'cat_qa'), 'Meowmeow', 'kushat'),
((SELECT id FROM users WHERE username = 'jack'), 'Misli admina', 'kushat i spat'),
((SELECT id FROM users WHERE username = 'lisa'), 'Misli moderatora', 'kushat i ne spat');

-- Попытка вставки с несуществующим user_id (ожидаемая ошибка)
-- INSERT INTO posts (user_id, title, body) VALUES (999, 'unreal', 'unreal');
-- Error: FOREIGN KEY constraint failed

-- 5. JOIN'ы
-- INNER JOIN: посты с авторами
SELECT posts.title, posts.body, users.username, users.email
FROM posts
INNER JOIN users ON posts.user_id = users.id;

-- LEFT JOIN: все посты с возможным NULL-автором
SELECT posts.title, posts.body, users.username
FROM posts
LEFT JOIN users ON posts.user_id = users.id;

-- Поиск орфанных постов (постов с несуществующим автором)
SELECT posts.id, posts.title, posts.user_id
FROM posts
LEFT JOIN users ON posts.user_id = users.id
WHERE users.id IS NULL;

-- Количество постов на пользователя (включая тех, у кого 0)
SELECT u.username, COUNT(p.id) AS post_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id;

-- 6. Подзапросы и CASE
-- Пользователи с постами (IN)
SELECT username, email FROM users WHERE id IN (SELECT user_id FROM posts);

-- Пользователи без постов (NOT IN)
SELECT username, email FROM users WHERE id NOT IN (SELECT DISTINCT user_id FROM posts);

-- EXISTS
SELECT * FROM users WHERE EXISTS (SELECT 1 FROM posts WHERE posts.user_id = users.id);

-- Классификация по возрасту
SELECT 
    username, 
    age,
    CASE
        WHEN age IS NULL THEN 'unknown'
        WHEN age < 18 THEN 'junior'
        WHEN age BETWEEN 18 AND 30 THEN 'middle'
        ELSE 'senior'
    END AS status
FROM users;

-- 7. Транзакции
-- Резервная копия
CREATE TABLE users_backup AS SELECT * FROM users;

-- ROLLBACK
BEGIN TRANSACTION;
DELETE FROM users_backup WHERE id = 3;
SELECT * FROM users_backup WHERE id = 3; -- пусто
ROLLBACK;
SELECT * FROM users_backup WHERE id = 3; -- запись вернулась

-- COMMIT
BEGIN TRANSACTION;
DELETE FROM users_backup WHERE id = 3;
COMMIT;
SELECT * FROM users_backup WHERE id = 3; -- пусто

-- Очистка
DROP TABLE users_backup;

-- 8. Каскадное удаление
-- До удаления пользователя sasha_qa
SELECT * FROM posts WHERE user_id = (SELECT id FROM users WHERE username = 'sasha_qa');

-- Удаляем пользователя
DELETE FROM users WHERE username = 'sasha_qa';

-- После удаления: посты пользователя sasha_qa исчезли
SELECT * FROM posts WHERE user_id = (SELECT id FROM users WHERE username = 'sasha_qa'); -- пустой результат
