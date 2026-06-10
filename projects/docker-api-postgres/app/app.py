# Импортируем класс Flask (фреймворк для создания веб-приложений)
from flask import Flask, jsonify  # jsonify превращает dict/list в JSON-ответ
# Импортируем библиотеку psycopg2 для работы с PostgreSQL
import psycopg2
# Импортируем модуль os для чтения переменных окружения
import os

# Создаём экземпляр Flask-приложения, __name__ – имя текущего модуля
app = Flask(__name__)

# Читаем параметры подключения к БД из переменных окружения (задаются в docker-compose.yml)
DB_HOST = os.environ['DB_HOST']  # имя хоста (сервиса) базы данных, у нас "db"
DB_NAME = os.environ['DB_NAME']  # имя базы данных, "products_db"
DB_USER = os.environ['DB_USER']  # пользователь БД, "qa"
DB_PASS = os.environ['DB_PASS']  # пароль пользователя, "qa123"

def get_db():
    """
    Создаёт и возвращает новое подключение к PostgreSQL.
    Каждый вызов открывает отдельное соединение, которое нужно закрывать.
    """
    # Устанавливаем соединение с БД, используя глобальные переменные
    return psycopg2.connect(
        host=DB_HOST,      # адрес сервера БД (контейнер "db")
        dbname=DB_NAME,    # имя базы данных
        user=DB_USER,      # имя пользователя
        password=DB_PASS   # пароль
    )

# Определяем маршрут GET /products (вернёт все товары)
@app.route('/products')
def products():
    # Получаем соединение с базой данных
    conn = get_db()
    # Создаём курсор для выполнения запросов
    cur = conn.cursor()
    # Выполняем SQL-запрос: выбрать все поля из таблицы products
    cur.execute('SELECT id, name, price FROM products;')
    # Извлекаем все строки результата (список кортежей)
    rows = cur.fetchall()
    # Закрываем курсор (освобождаем ресурсы)
    cur.close()
    # Закрываем соединение с БД (важно, чтобы не было утечек)
    conn.close()

    # Преобразуем каждую строку в словарь: r[0] – id, r[1] – name, r[2] – price
    # price преобразуем во float для корректного JSON (Decimal из БД не сериализуется)
    result = [{'id': r[0], 'name': r[1], 'price': float(r[2])} for r in rows]
    # Возвращаем JSON-ответ со списком товаров (HTTP статус 200 по умолчанию)
    return jsonify(result)

# Определяем маршрут GET /products/<int:id> – получение товара по id
@app.route('/products/<int:id>')
def product_by_id(id):
    # Открываем соединение с БД
    conn = get_db()
    # Создаём курсор
    cur = conn.cursor()
    # Параметризованный запрос: %s – плейсхолдер, (id,) – кортеж параметров
    # Безопасно, SQL-инъекции исключены
    cur.execute('SELECT id, name, price FROM products WHERE id = %s;', (id,))
    # Получаем одну строку (или None, если товара с таким id нет)
    row = cur.fetchone()
    # Закрываем курсор
    cur.close()
    # Закрываем соединение
    conn.close()

    # Если товар не найден
    if row is None:
        # Возвращаем JSON с ошибкой и HTTP-статус 404 (Not Found)
        return jsonify({'error': 'Product not found'}), 404

    # Если товар найден, возвращаем его в JSON (статус 200)
    return jsonify({'id': row[0], 'name': row[1], 'price': float(row[2])})

# Точка входа: если скрипт запущен напрямую (не импортирован как модуль)
if __name__ == '__main__':
    # Запускаем встроенный сервер разработки Flask
    # host='0.0.0.0' – слушаем все сетевые интерфейсы (чтобы был доступен извне контейнера)
    # port=5000 – порт, на котором будет работать сервер
    app.run(host='0.0.0.0', port=5000)
