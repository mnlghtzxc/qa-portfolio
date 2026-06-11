Cinema Ticket Purchase API — Документация
Версия API: v1
Базовый URL: http://localhost:5000/api/v1

Аутентификация
На данный момент не требуется.

Формат ответов
Все ответы возвращаются в формате JSON.

Успешный ответ:

data — содержит запрашиваемые данные

message — для операций создания/обновления/удаления

Ошибочный ответ:

error — описание ошибки

details (опционально) — технические подробности

Клиентские эндпоинты (Client)
1. Список сеансов (витрина)
GET /sessions

Возвращает список всех сеансов с количеством свободных мест.

Параметры запроса (query string, опционально):

movie_id — отфильтровать по ID фильма

date — отфильтровать по дате в формате YYYY-MM-DD

Пример запроса:

bash
curl http://localhost:5000/api/v1/sessions
Успешный ответ (200):

json
{
  "sessions": [
    {
      "session_id": 1,
      "movie": "The Lord of the Rings",
      "duration_minutes": 176,
      "hall": "IMAX",
      "capacity": 50,
      "tickets_sold": 3,
      "free_seats": 47,
      "start_time": "2027-06-11 20:00:00",
      "end_time": "2027-06-11 22:56:00"
    }
  ]
}
2. Покупка билета
POST /tickets/purchase

Создаёт билет на указанный сеанс. Цена определяется автоматически по базовой цене зала. Требуется указать либо user_id (для зарегистрированного пользователя), либо email (для анонимной покупки), но не оба одновременно.

Тело запроса (JSON):

json
{
  "session_id": 1,
  "user_id": 1,
  "email": null
}
или

json
{
  "session_id": 1,
  "email": "guest@example.com"
}
Обязательные поля:

session_id (integer) — ID сеанса

Условно обязательные (ровно одно из двух):

user_id (integer|null) — ID зарегистрированного пользователя

email (string|null) — email анонимного покупателя

Возможные ответы:

201 Created — билет успешно куплен

json
{
  "message": "Ticket purchased successfully",
  "ticket": {
    "id": 5,
    "session_id": 1,
    "customer_id": 3,
    "price": 500.0,
    "status": "purchased",
    "created_at": "2026-06-11 15:49:01"
  }
}
400 Bad Request — ошибка валидации

json
{
  "error": "Provide either user_id or email, but not both"
}
404 Not Found — сеанс или пользователь не найден

json
{
  "error": "Session not found"
}
409 Conflict — нет свободных мест

json
{
  "error": "No available seats for this session"
}
3. Возврат билета
POST /tickets/{ticket_id}/refund

Меняет статус билета на refund. Допустим только если билет в статусе purchased и сеанс ещё не начался.

Параметры пути:

ticket_id (integer) — ID билета

Пример запроса:

bash
curl -X POST http://localhost:5000/api/v1/tickets/4/refund
Возможные ответы:

200 OK — билет успешно возвращён

json
{
  "message": "Ticket refunded successfully",
  "ticket": {
    "id": 4,
    "status": "refund",
    "created_at": "2026-06-11 15:48:45"
  }
}
400 Bad Request — неверный статус или сеанс уже начался

json
{
  "error": "Ticket cannot be refunded. Current status: used"
}
json
{
  "error": "Cannot refund ticket: session has already started"
}
404 Not Found — билет не существует

json
{
  "error": "Ticket not found"
}
4. Билеты пользователя
GET /users/{user_id}/tickets

Возвращает список всех билетов, купленных зарегистрированным пользователем.

Параметры пути:

user_id (integer) — ID пользователя

Пример запроса:

bash
curl http://localhost:5000/api/v1/users/1/tickets
Успешный ответ (200):

json
{
  "user_id": 1,
  "tickets": [
    {
      "ticket_id": 4,
      "session_id": 1,
      "movie": "The Lord of the Rings",
      "hall": "IMAX",
      "start_time": "2027-06-11 20:00:00",
      "end_time": "2027-06-11 22:56:00",
      "price": 500.0,
      "status": "refund",
      "purchased_at": "2026-06-11 15:48:45"
    }
  ]
}
404 Not Found — пользователь не найден

json
{
  "error": "User not found"
}
Административные эндпоинты (Admin)
Залы (Halls)
Список залов
GET /admin/halls

json
{
  "halls": [
    {
      "id": 1,
      "name": "IMAX",
      "capacity": 50,
      "base_price": 500.0
    }
  ]
}
Создание зала
POST /admin/halls

Тело запроса:

json
{
  "name": "Lounge",
  "capacity": 15,
  "base_price": 1200.00
}
201 Created — успех

400 Bad Request — неверные параметры

Фильмы (Movies)
Список фильмов
GET /admin/movies

Добавление фильма
POST /admin/movies

Тело запроса:

json
{
  "title": "Interstellar",
  "duration_minutes": 169,
  "genre": "Sci-Fi"
}
Частичное обновление фильма (PATCH)
PATCH /admin/movies/{movie_id}

Можно передать только изменяемые поля (title, duration_minutes, genre).

Тело запроса (пример):

json
{
  "title": "The Lord of the Rings"
}
Удаление фильма
DELETE /admin/movies/{movie_id}

200 OK — фильм удалён

409 Conflict — нельзя удалить фильм, на который есть сеансы

Сеансы (Sessions)
Создание сеанса
POST /admin/sessions

Тело запроса:

json
{
  "movie_id": 2,
  "hall_id": 2,
  "start_time": "2027-06-12 20:00:00"
}
Поле end_time вычисляется автоматически: start_time + длительность фильма.

Дополнительная валидация: зал не должен быть занят другим сеансом в это же время.

201 Created — успех

409 Conflict — зал занят

404 Not Found — фильм или зал не существует

400 Bad Request — неверный формат времени

Проверка работоспособности
GET /health

json
{
  "status": "ok",
  "message": "Server is running"
}
Коды ошибок
Код	Значение
200	Успех
201	Создано
400	Неверный запрос (валидация)
404	Не найдено
409	Конфликт (нет мест, зал занят)
500	Внутренняя ошибка сервера
