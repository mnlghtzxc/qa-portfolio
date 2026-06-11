INSERT INTO halls (name, capacity, base_price) VALUES ('IMAX', 50, 500.00),
                                          ('3D', 25, 350.00),
                                          ('VIP', 10, 700.00);   -- Добавили 3 зала imax, 3d, vip в таблицу halls

INSERT INTO movies (title, duration_minutes, genre) VALUES ('Lord of the rings', 176, 'Fantasy'),
                                                           ('Matrix', 115, 'Sci-fi'),
 						           ('Dark knight', 133, 'Action'),
                                                           ('Forrest Gump', 142, 'Drama'),
                                                           ('Hangover', 100, 'Comedy');   -- Добавили 5 фильмов в таблицу movies

INSERT INTO users (name, email) VALUES ('Vlad', 'vlad@qwe.com'),
                                       ('Julia', 'julia@qwe.com'),
                                       ('Pavel', 'pavel@qwe.com'),
                                       ('Jack', 'jack@qwe.com'),
                                       ('Lisa', 'lisa@qwe.com');   -- Добавили 5 юзеров в таблицу users

INSERT INTO customers (user_id, email) VALUES (1, 'vlad@qwe.com'),
                                              (NULL, 'anonim@qwe.com');   -- Добавили данные в таблицу customers

INSERT INTO sessions (movie_id, hall_id, start_time, end_time) VALUES (1, 1, '2027-06-11 20:00:00', '2027-06-11 22:56:00'),
                                                                      (5, 3, '2025-01-01 00:00:00', '2025-01-01 01:40:00');   -- Добавили сессии в будущем и прошлом

INSERT INTO tickets (session_id, customer_id, price, status) VALUES (1, 1, 450.00, 'purchased'),   -- Влад купил билет на властелин колец за 450.00
                                                                    (2, 2, 350.00, 'used'),   -- Аноним купил билет на мальчишник за 350.00, билет уже использован, значит сеанс в прошлом
                                                                    (2, 1, 600.00, 'refund');   -- Влад купил билет в Vip на мальчишник, но сделал возврат
