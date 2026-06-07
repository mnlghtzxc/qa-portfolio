#!/bin/bash
# 👆 Это "шебанг" (shebang). Он указывает системе, что файл нужно выполнять через интерпретатор Bash.

# 1. Проверяем, передан ли первый аргумент ($1 - базовый URL)
if [ -z "$1" ]; then
    echo "Ошибка: Не указан базовый URL!"
    echo "Использование: $0 <base_url>"
    exit 1 # Выходим из скрипта с кодом ошибки
fi

BASE_URL=$1 # Записываем аргумент в понятную переменную

# Флаг-индикатор: если хоть один тест упадет, мы поменяем его значение на 1
FAILED=0

echo "=== Запуск Smoke-тестов для $BASE_URL ==="

# 2. Создаем массив эндпоинтов для проверки
# Формат элемента: "эндпоинт:ожидаемый_статус:искомая_строка"
ENDPOINTS=(
    "/posts/1:200:title"
    "/users/1:200:email"
    "/posts/99999:404:NOT_FOUND" # Для 404 строку можно искать любую абстрактную, главное — проверить статус
)

# 3. Запускаем цикл для обхода массива
for item in "${ENDPOINTS[@]}"; do
    # Разрезаем строку элемента по двоеточию на отдельные переменные
    ENDPOINT=$(echo "$item" | cut -d':' -f1)
    EXPECTED_STATUS=$(echo "$item" | cut -d':' -f2)
    PATTERN=$(echo "$item" | cut -d':' -f3)

    FULL_URL="${BASE_URL}${ENDPOINT}"

    # Делаем запрос через curl: вытаскиваем статус-код
    # Нам также нужно тело, поэтому сохраняем его во временную переменную
    # Способ получить и статус, и тело:
    RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$FULL_URL")
    
    # Парсим статус-код и чистое тело из ответа
    ACTUAL_STATUS=$(echo "$RESPONSE" | tr '\n' ' ' | grep -o 'HTTP_STATUS:[0-9]\+' | cut -d':' -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

    # Проверяем условия
    if [ "$ACTUAL_STATUS" != "$EXPECTED_STATUS" ]; then
        # Если статус не совпал — это FAIL
        echo "[FAIL] $ENDPOINT - expected $EXPECTED_STATUS got $ACTUAL_STATUS"
        FAILED=1
    else
        # Если статус совпал, проверяем тело (только для позитивных тестов со статусом 200) []
        if [ "$EXPECTED_STATUS" = "200" ]; then
            # Ищем паттерн в теле ответа []
            if echo "$BODY" | grep -q "$PATTERN"; then
                echo "[PASS] $ENDPOINT"
            else
                echo "[FAIL] $ENDPOINT - expected keyword '$PATTERN' missing in body"
                FAILED=1
            fi
        else
            # Для негативных тестов (например, 404), если статус ок — тест пройден
            echo "[PASS] $ENDPOINT"
        fi
    fi
done

echo "======================================="

# 4. Финальный вывод на основе флага FAILED
if [ "$FAILED" -eq 0 ]; then
    echo "All tests passed"
else
    echo "Some tests failed"
    exit 1
fi
