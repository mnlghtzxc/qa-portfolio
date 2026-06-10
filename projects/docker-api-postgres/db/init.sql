CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price NUMERIC(10,2)
);

INSERT INTO products (name, price) VALUES
('Widget', 9.99),
('Gadget', 19.99),
('Doohickey', 4.49);