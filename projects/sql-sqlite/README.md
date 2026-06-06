# SQL для QA: проверка целостности данных и анализ

## 🎯 Цель
Продемонстрировать навыки работы с реляционными базами данных через призму задач QA-инженера: проверка целостности, поиск аномалий, подготовка данных для расследования инцидентов.

## 🧠 Ключевые навыки
- Проектирование таблиц и ограничений (PRIMARY KEY, UNIQUE, NOT NULL, FOREIGN KEY)
- Написание запросов CRUD
- Фильтрация и поиск (WHERE, LIKE, AND/OR)
- Агрегация и группировка (GROUP BY, HAVING, COUNT, AVG)
- Объединения (INNER JOIN, LEFT JOIN)
- Поиск «битых» связей и орфанных записей
- Подзапросы (IN, EXISTS) и условная логика (CASE)
- Транзакции (BEGIN, COMMIT, ROLLBACK)

## 🛠️ Инструменты
- SQLite 3 (консольный клиент)
- Локальная тестовая БД (`test.db`)
- Конфигурационный файл `sqlite_config.txt` для воспроизводимого вывода
- Все запросы собраны в `queries.sql` с подробными комментариями

## 📦 Описание тестовой базы
База содержит две связанные таблицы:

**users** — пользователи сервиса  
| Поле | Тип | Ограничения |
|------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| username | TEXT | NOT NULL |
| email | TEXT | UNIQUE NOT NULL |
| registered_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| role | TEXT | NOT NULL DEFAULT 'user' |
| age | INTEGER | |

**posts** — посты пользователей  
| Поле | Тип | Ограничения |
|------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| user_id | INTEGER | NOT NULL, FOREIGN KEY REFERENCES users(id) ON DELETE CASCADE |
| title | TEXT | NOT NULL |
| body | TEXT | |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

Связь `posts.user_id → users.id` настроена с каскадным удалением: при удалении пользователя его посты автоматически удаляются, что гарантирует целостность данных.

## 🧪 Сценарий для QA: как я проверяю данные после API-запроса
1. После выполнения POST-запроса на создание пользователя через API выполняю `SELECT * FROM users WHERE email = 'new@example.com';` чтобы убедиться, что запись появилась, поля заполнены корректно, дата регистрации проставлена.
2. После выполнения DELETE-запроса проверяю, что запись действительно удалена (`SELECT COUNT(*) FROM users WHERE id = ...`), а связанные посты удалены каскадно.
3. Периодически запускаю «санитарные» запросы:
   - `SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1;` — нет ли дубликатов в уникальной колонке.
   - `SELECT p.id, p.user_id FROM posts p LEFT JOIN users u ON p.user_id = u.id WHERE u.id IS NULL;` — нет ли постов, ссылающихся на несуществующего пользователя (орфанов).
   - Проверяю средние значения, минимальные/максимальные id, распределение по ролям.

## 📂 Структура проекта
- [`queries.sql`](./queries.sql) — полный набор запросов с комментариями
- [`sqlite_config.txt`](./sqlite_config.txt) — настройки отображения и поведения SQLite
- [`screenshots`](./screenshots) — скриншоты результатов ключевых запросов

## 🖼️ Скриншоты
1. [`select_all_users_and_posts.png`](./screenshots/select_all_users_and_posts.png) — вывод всех пользователей
2. [`group_by_role.png`](./screenshots/group_by_role.png) — группировка по ролям с подсчётом
3. [`left_join_orphans.png`](./screenshots/left_join_orphans.png) — поиск потерянных связей
4. [`rollback.png`](./screenshots/rollback.png) — демонстрация отката транзакции
5. [`cascade_delete.png`](./screenshots/cascade_delete.png) — каскадное удаление поста при удалении пользователя
