from flask import Flask, jsonify
import psycopg2
import os

app = Flask(__name__)

DB_HOST = os.environ['DB_HOST']
DB_NAME = os.environ['DB_NAME']
DB_USER = os.environ['DB_USER']
DB_PASS = os.environ['DB_PASS']

def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

@app.route('/products')
def products():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, name, price FROM products;')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    result = [{'id': r[0], 'name': r[1], 'price': float(r[2])} for r in rows]
    return jsonify(result)

@app.route('/products/<int:id>')
def product_by_id(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, name, price FROM products WHERE id = %s;', (id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({'id': row[0], 'name': row[1], 'price': float(row[2])})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)