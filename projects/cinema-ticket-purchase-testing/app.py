"""
cinema-ticket-purchase-testing/app.py
Основной файл Flask-приложения для проекта "Продажа билетов в кинотеатр".
Поднимает REST API, который взаимодействует с PostgreSQL.
"""

from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# ------------------------------------------------------------
# Настройки подключения к базе данных
# Берём из переменных окружения, если их нет — используем значения по умолчанию
# ------------------------------------------------------------
DB_USER = os.getenv('DB_USER', 'cinema_admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'cinema_pass')
DB_HOST = os.getenv('DB_HOST', 'localhost')    # т.к. база проброшена на порт 5432 хоста
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'cinema_db')

def get_db_connection():
    """
    Открывает новое соединение с PostgreSQL и возвращает объект connection.
    Все настройки берутся из глобальных переменных выше.
    """
    conn = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )
    return conn

# ------------------------------------------------------------
# Маршрут: проверка работоспособности сервера
# ------------------------------------------------------------
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """
    Самый простой эндпоинт, не требует подключения к БД.
    Возвращает JSON с подтверждением, что сервер жив.
    """
    return jsonify({'status': 'ok', 'message': 'Server is running'}), 200

# ------------------------------------------------------------
# Маршрут: список сеансов с доступными местами
# ------------------------------------------------------------
@app.route('/api/v1/sessions', methods=['GET'])
def get_sessions():
    """
    Возвращает список всех сеансов в формате JSON.
    Для каждого сеанса вычисляется количество свободных мест:
    вместимость зала минус количество купленных и использованных билетов.
    """
    # Шаг 1. Открываем соединение с базой данных
    conn = get_db_connection()
    # Шаг 2. Создаём курсор, который будет возвращать строки как словари
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Шаг 3. Пишем SQL-запрос, который собирает данные из четырёх таблиц
    query = """
        SELECT
            s.id AS session_id,
            m.title AS movie_title,
            m.duration_minutes,
            h.name AS hall_name,
            h.capacity,
            s.start_time,
            s.end_time,
            -- Подсчитываем количество купленных (purchased) и использованных (used) билетов
            -- Билеты со статусом 'refund' не учитываются, места возвращаются в продажу
            COUNT(t.id) FILTER (WHERE t.status IN ('purchased', 'used')) AS tickets_sold
        FROM sessions s
        -- Соединяем сеанс с фильмом, чтобы получить название и длительность
        JOIN movies m ON s.movie_id = m.id
        -- Соединяем сеанс с залом, чтобы получить вместимость и название зала
        JOIN halls h ON s.hall_id = h.id
        -- LEFT JOIN нужен, чтобы не потерять сеансы, на которые ещё не куплено ни одного билета
        LEFT JOIN tickets t ON s.id = t.session_id
        GROUP BY s.id, m.title, m.duration_minutes, h.name, h.capacity, s.start_time, s.end_time
        ORDER BY s.start_time;
    """

    # Шаг 4. Выполняем запрос
    cur.execute(query)
    # Шаг 5. Получаем все строки результата в виде списка словарей
    sessions = cur.fetchall()

    # Шаг 6. Преобразуем результат: вычисляем свободные места и формируем понятный JSON
    result = []
    for row in sessions:
        free_seats = row['capacity'] - row['tickets_sold']
        result.append({
            'session_id': row['session_id'],
            'movie': row['movie_title'],
            'duration_minutes': row['duration_minutes'],
            'hall': row['hall_name'],
            'capacity': row['capacity'],
            'tickets_sold': row['tickets_sold'],
            'free_seats': free_seats,
            'start_time': row['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': row['end_time'].strftime('%Y-%m-%d %H:%M:%S')
        })

    # Шаг 7. Закрываем курсор и соединение, освобождаем ресурсы
    cur.close()
    conn.close()

    # Шаг 8. Возвращаем результат в виде JSON с кодом 200
    return jsonify({'sessions': result}), 200

# ------------------------------------------------------------
# Маршрут: покупка билета
# ------------------------------------------------------------
@app.route('/api/v1/tickets/purchase', methods=['POST'])
def purchase_ticket():
    """
    Покупает билет на указанный сеанс.
    Ожидает JSON с полями:
    - session_id (обязательно)
    - user_id (опционально, если покупатель зарегистрирован)
    - email (опционально, если покупка анонимная)
    Правило: должно быть заполнено либо user_id, либо email.
    Цена билета автоматически берётся из таблицы halls (поле base_price).
    """
    # Шаг 1. Получаем данные из тела запроса
    data = request.get_json()
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    email = data.get('email')

    # Шаг 2. Валидация: session_id обязателен
    if not session_id:
        return jsonify({'error': 'session_id is required'}), 400

    # Шаг 3. Валидация: ровно одно из user_id/email должно быть заполнено
    if (user_id is None and email is None) or (user_id is not None and email is not None):
        return jsonify({'error': 'Provide either user_id (for registered users) or email (for anonymous buyers), but not both'}), 400

    # Шаг 4. Открываем соединение с БД
    conn = get_db_connection()
    # Используем RealDictCursor для удобной работы со словарями
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Шаг 5. Начинаем транзакцию
        # Это гарантирует, что проверка мест и вставка билета выполнятся атомарно
        conn.autocommit = False

        # Шаг 6. Блокируем строку сеанса, чтобы никто не изменил данные параллельно
        #      и проверяем существование сеанса
        cur.execute("SELECT id FROM sessions WHERE id = %s FOR UPDATE", (session_id,))
        session = cur.fetchone()
        if not session:
            conn.rollback()
            return jsonify({'error': 'Session not found'}), 404

        # Шаг 7. Получаем вместимость зала и базовую цену
        cur.execute("""
            SELECT h.capacity, h.base_price
            FROM sessions s
            JOIN halls h ON s.hall_id = h.id
            WHERE s.id = %s
        """, (session_id,))
        hall_info = cur.fetchone()
        capacity = hall_info['capacity']
        base_price = float(hall_info['base_price'])

        # Шаг 8. Считаем количество проданных (активных) билетов на этот сеанс
        cur.execute("""
            SELECT COUNT(*) AS sold
            FROM tickets
            WHERE session_id = %s AND status IN ('purchased', 'used')
        """, (session_id,))
        sold = cur.fetchone()['sold']

        # Шаг 9. Проверяем, есть ли свободные места
        if sold >= capacity:
            conn.rollback()
            return jsonify({'error': 'No available seats for this session'}), 409  # Conflict

        # Шаг 10. Работаем с покупателем (customers)
        customer_id = None
        if user_id is not None:
            # Зарегистрированный пользователь: проверяем, что такой user существует
            cur.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user:
                conn.rollback()
                return jsonify({'error': 'User not found'}), 404

            # Ищем покупателя (customer) по user_id
            cur.execute("SELECT id FROM customers WHERE user_id = %s", (user_id,))
            customer = cur.fetchone()
            if not customer:
                # Если покупателя ещё нет, создаём его, копируя email из users
                cur.execute(
                    "INSERT INTO customers (user_id, email) VALUES (%s, %s) RETURNING id",
                    (user_id, user['email'])
                )
                customer = cur.fetchone()
            customer_id = customer['id']
        else:
            # Анонимный покупатель: ищем по email
            cur.execute("SELECT id FROM customers WHERE email = %s AND user_id IS NULL", (email,))
            customer = cur.fetchone()
            if not customer:
                # Создаём нового анонимного покупателя
                cur.execute(
                    "INSERT INTO customers (user_id, email) VALUES (NULL, %s) RETURNING id",
                    (email,)
                )
                customer = cur.fetchone()
            customer_id = customer['id']

        # Шаг 11. Создаём билет со статусом 'purchased' и ценой из зала
        cur.execute("""
            INSERT INTO tickets (session_id, customer_id, price, status)
            VALUES (%s, %s, %s, 'purchased')
            RETURNING id, price, status, created_at
        """, (session_id, customer_id, base_price))
        ticket = cur.fetchone()

        # Шаг 12. Фиксируем транзакцию
        conn.commit()

        # Шаг 13. Формируем ответ
        return jsonify({
            'message': 'Ticket purchased successfully',
            'ticket': {
                'id': ticket['id'],
                'session_id': session_id,
                'customer_id': customer_id,
                'price': float(ticket['price']),
                'status': ticket['status'],
                'created_at': ticket['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 201  # Created

    except Exception as e:
        # Шаг 14. Если что-то пошло не так, откатываем все изменения
        conn.rollback()
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

    finally:
        # Шаг 15. Закрываем курсор и соединение в любом случае
        cur.close()
        conn.close()

# ------------------------------------------------------------
# Маршрут: возврат билета
# ------------------------------------------------------------
@app.route('/api/v1/tickets/<int:ticket_id>/refund', methods=['POST'])
def refund_ticket(ticket_id):
    """
    Возвращает билет (меняет статус на 'refund').
    Проверяет, что билет существует, имеет статус 'purchased',
    и что сеанс ещё не начался.
    """
    # Шаг 1. Открываем соединение с БД
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Шаг 2. Начинаем транзакцию и блокируем строку билета, чтобы избежать гонок
        conn.autocommit = False
        cur.execute("SELECT id FROM tickets WHERE id = %s FOR UPDATE", (ticket_id,))
        ticket_exists = cur.fetchone()
        if not ticket_exists:
            conn.rollback()
            return jsonify({'error': 'Ticket not found'}), 404

        # Шаг 3. Получаем статус билета и время начала сеанса
        cur.execute("""
            SELECT t.status, s.start_time
            FROM tickets t
            JOIN sessions s ON t.session_id = s.id
            WHERE t.id = %s
        """, (ticket_id,))
        ticket_info = cur.fetchone()

        # Шаг 4. Проверяем статус билета: только 'purchased' можно вернуть
        if ticket_info['status'] != 'purchased':
            conn.rollback()
            return jsonify({'error': 'Ticket cannot be refunded. Current status: ' + ticket_info['status']}), 400

        # Шаг 5. Проверяем, что сеанс ещё не начался (дата начала в будущем)
        if ticket_info['start_time'] <= datetime.now():
            conn.rollback()
            return jsonify({'error': 'Cannot refund ticket: session has already started'}), 400

        # Шаг 6. Обновляем статус билета на 'refund'
        cur.execute("""
            UPDATE tickets SET status = 'refund' WHERE id = %s
            RETURNING id, status, created_at
        """, (ticket_id,))
        updated_ticket = cur.fetchone()

        # Шаг 7. Фиксируем транзакцию
        conn.commit()

        # Шаг 8. Формируем ответ
        return jsonify({
            'message': 'Ticket refunded successfully',
            'ticket': {
                'id': updated_ticket['id'],
                'status': updated_ticket['status'],
                'created_at': updated_ticket['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

    finally:
        cur.close()
        conn.close()

# ------------------------------------------------------------
# Маршрут: билеты пользователя
# ------------------------------------------------------------
@app.route('/api/v1/users/<int:user_id>/tickets', methods=['GET'])
def get_user_tickets(user_id):
    """
    Возвращает список билетов, купленных пользователем.
    Проходит по цепочке: users -> customers -> tickets.
    Выводит детали билета, сеанса и фильма.
    """
    # Шаг 1. Открываем соединение
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Шаг 2. Проверяем, существует ли пользователь
        cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Шаг 3. Находим покупателя (customers), связанного с этим пользователем
        cur.execute("SELECT id FROM customers WHERE user_id = %s", (user_id,))
        customer = cur.fetchone()
        if not customer:
            # У пользователя может не быть покупок — возвращаем пустой список
            return jsonify({'user_id': user_id, 'tickets': []}), 200

        # Шаг 4. Получаем все билеты этого покупателя с информацией о сеансе и фильме
        cur.execute("""
            SELECT
                t.id AS ticket_id,
                t.price,
                t.status,
                t.created_at,
                s.id AS session_id,
                s.start_time,
                s.end_time,
                m.title AS movie_title,
                m.duration_minutes,
                h.name AS hall_name
            FROM tickets t
            JOIN sessions s ON t.session_id = s.id
            JOIN movies m ON s.movie_id = m.id
            JOIN halls h ON s.hall_id = h.id
            WHERE t.customer_id = %s
            ORDER BY t.created_at DESC
        """, (customer['id'],))
        tickets = cur.fetchall()

        # Шаг 5. Формируем ответ
        result = []
        for t in tickets:
            result.append({
                'ticket_id': t['ticket_id'],
                'session_id': t['session_id'],
                'movie': t['movie_title'],
                'hall': t['hall_name'],
                'start_time': t['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': t['end_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'price': float(t['price']),
                'status': t['status'],
                'purchased_at': t['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify({
            'user_id': user_id,
            'tickets': result
        }), 200

    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

    finally:
        cur.close()
        conn.close()

# ------------------------------------------------------------
# АДМИНИСТРАТИВНЫЕ МАРШРУТЫ
# ------------------------------------------------------------

# ---------- ЗАЛЫ ----------

@app.route('/api/v1/admin/halls', methods=['GET'])
def get_halls():
    """Возвращает список всех залов."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute("SELECT id, name, capacity, base_price FROM halls ORDER BY id;")
        halls = cur.fetchall()
        # Преобразуем Decimal в float для JSON
        for hall in halls:
            hall['base_price'] = float(hall['base_price'])
        return jsonify({'halls': halls}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/v1/admin/halls', methods=['POST'])
def create_hall():
    """Создаёт новый зал. Ожидает JSON: { "name": "...", "capacity": 50, "base_price": 500.00 }"""
    data = request.get_json()
    name = data.get('name')
    capacity = data.get('capacity')
    base_price = data.get('base_price')

    # Простейшая валидация
    if not name or not capacity or not base_price:
        return jsonify({'error': 'name, capacity and base_price are required'}), 400
    if capacity <= 0 or base_price <= 0:
        return jsonify({'error': 'capacity and base_price must be positive'}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "INSERT INTO halls (name, capacity, base_price) VALUES (%s, %s, %s) RETURNING id, name, capacity, base_price;",
            (name, capacity, base_price)
        )
        new_hall = cur.fetchone()
        conn.commit()
        new_hall['base_price'] = float(new_hall['base_price'])
        return jsonify({'message': 'Hall created', 'hall': new_hall}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# ---------- ФИЛЬМЫ ----------

@app.route('/api/v1/admin/movies', methods=['GET'])
def get_movies():
    """Возвращает список всех фильмов."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute("SELECT id, title, duration_minutes, genre FROM movies ORDER BY id;")
        movies = cur.fetchall()
        return jsonify({'movies': movies}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/v1/admin/movies', methods=['POST'])
def create_movie():
    """Добавляет новый фильм. Ожидает JSON: { "title": "...", "duration_minutes": 120, "genre": "..." }"""
    data = request.get_json()
    title = data.get('title')
    duration_minutes = data.get('duration_minutes')
    genre = data.get('genre')

    if not title or not duration_minutes or not genre:
        return jsonify({'error': 'title, duration_minutes and genre are required'}), 400
    if duration_minutes <= 0:
        return jsonify({'error': 'duration_minutes must be positive'}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "INSERT INTO movies (title, duration_minutes, genre) VALUES (%s, %s, %s) RETURNING id, title, duration_minutes, genre;",
            (title, duration_minutes, genre)
        )
        new_movie = cur.fetchone()
        conn.commit()
        return jsonify({'message': 'Movie created', 'movie': new_movie}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/v1/admin/movies/<int:movie_id>', methods=['PATCH'])
def update_movie(movie_id):
    """Обновляет фильм. Можно передать любые поля: title, duration_minutes, genre."""
    data = request.get_json()
    # Собираем SET-часть запроса динамически
    fields = []
    values = []
    for field in ['title', 'duration_minutes', 'genre']:
        if field in data:
            fields.append(f"{field} = %s")
            values.append(data[field])
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400

    values.append(movie_id)
    query = f"UPDATE movies SET {', '.join(fields)} WHERE id = %s RETURNING id, title, duration_minutes, genre;"

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(query, values)
        updated_movie = cur.fetchone()
        if not updated_movie:
            conn.rollback()
            return jsonify({'error': 'Movie not found'}), 404
        conn.commit()
        return jsonify({'message': 'Movie updated', 'movie': updated_movie}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/v1/admin/movies/<int:movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    """Удаляет фильм, если на него нет сеансов."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Проверяем, есть ли сеансы с этим фильмом
        cur.execute("SELECT COUNT(*) FROM sessions WHERE movie_id = %s;", (movie_id,))
        count = cur.fetchone()[0]
        if count > 0:
            conn.rollback()
            return jsonify({'error': 'Cannot delete movie with active sessions'}), 409

        cur.execute("DELETE FROM movies WHERE id = %s RETURNING id;", (movie_id,))
        deleted = cur.fetchone()
        if not deleted:
            conn.rollback()
            return jsonify({'error': 'Movie not found'}), 404
        conn.commit()
        return jsonify({'message': 'Movie deleted'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# ---------- СЕАНСЫ ----------

@app.route('/api/v1/admin/sessions', methods=['POST'])
def create_session():
    """
    Создаёт новый сеанс.
    Ожидает JSON: { "movie_id": 1, "hall_id": 1, "start_time": "2027-06-12 18:00:00" }
    end_time рассчитывается автоматически: start_time + duration_minutes.
    Проверяет, что зал свободен в это время (нет пересечения с другими сеансами).
    """
    data = request.get_json()
    movie_id = data.get('movie_id')
    hall_id = data.get('hall_id')
    start_time_str = data.get('start_time')

    if not movie_id or not hall_id or not start_time_str:
        return jsonify({'error': 'movie_id, hall_id and start_time are required'}), 400

    # Парсим start_time
    try:
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({'error': 'start_time must be in format YYYY-MM-DD HH:MM:SS'}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        conn.autocommit = False

        # Получаем длительность фильма
        cur.execute("SELECT duration_minutes FROM movies WHERE id = %s;", (movie_id,))
        movie = cur.fetchone()
        if not movie:
            conn.rollback()
            return jsonify({'error': 'Movie not found'}), 404

        duration = movie['duration_minutes']
        end_time = start_time + timedelta(minutes=duration)

        # Проверяем, что зал существует
        cur.execute("SELECT id FROM halls WHERE id = %s;", (hall_id,))
        if not cur.fetchone():
            conn.rollback()
            return jsonify({'error': 'Hall not found'}), 404

        # Проверяем пересечение с другими сеансами в этом зале
        cur.execute("""
            SELECT COUNT(*) FROM sessions
            WHERE hall_id = %s
              AND start_time < %s
              AND end_time > %s;
        """, (hall_id, end_time, start_time))
        if cur.fetchone()['count'] > 0:
            conn.rollback()
            return jsonify({'error': 'Hall is already booked for this time slot'}), 409

        # Создаём сеанс
        cur.execute(
            "INSERT INTO sessions (movie_id, hall_id, start_time, end_time) VALUES (%s, %s, %s, %s) RETURNING id, movie_id, hall_id, start_time, end_time;",
            (movie_id, hall_id, start_time, end_time)
        )
        session = cur.fetchone()
        conn.commit()

        return jsonify({
            'message': 'Session created',
            'session': {
                'id': session['id'],
                'movie_id': session['movie_id'],
                'hall_id': session['hall_id'],
                'start_time': session['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': session['end_time'].strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/admin/halls/<int:hall_id>', methods=['DELETE'])
def delete_hall(hall_id):
    """Удаляет зал, если на него нет сеансов."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM sessions WHERE hall_id = %s;", (hall_id,))
        if cur.fetchone()[0] > 0:
            conn.rollback()
            return jsonify({'error': 'Cannot delete hall with active sessions'}), 409

        cur.execute("DELETE FROM halls WHERE id = %s RETURNING id;", (hall_id,))
        if cur.fetchone() is None:
            conn.rollback()
            return jsonify({'error': 'Hall not found'}), 404
        conn.commit()
        return jsonify({'message': 'Hall deleted'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/v1/admin/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Удаляет сеанс, если на него нет проданных (purchased/used) билетов."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM tickets WHERE session_id = %s AND status IN ('purchased','used');", (session_id,))
        if cur.fetchone()[0] > 0:
            conn.rollback()
            return jsonify({'error': 'Cannot delete session with active tickets'}), 409

        cur.execute("DELETE FROM sessions WHERE id = %s RETURNING id;", (session_id,))
        if cur.fetchone() is None:
            conn.rollback()
            return jsonify({'error': 'Session not found'}), 404
        conn.commit()
        return jsonify({'message': 'Session deleted'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# ------------------------------------------------------------
# Точка входа: запуск приложения
# ------------------------------------------------------------
if __name__ == '__main__':
    # debug=True включает авто-перезагрузку при изменениях кода
    # host='0.0.0.0' делает сервер доступным снаружи контейнера/хоста
    app.run(debug=True, host='0.0.0.0', port=5000)
