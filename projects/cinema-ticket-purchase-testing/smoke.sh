#!/bin/bash

# Cinema Ticket Purchase API — Smoke-проверки
# Запускается вручную, проверяет доступность эндпоинтов.
# Использует curl и grep. Выводит PASS или FAIL.


BASE_URL="http://localhost:5000/api/v1"
PASS=0
FAIL=0

check() {
    local description="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local expected="$5"

    if [ "$method" == "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" \
            -H "Content-Type: application/json" -d "$data")
    fi

    if echo "$response" | grep -q "$expected"; then
        echo "[PASS] $description"
        PASS=$((PASS+1))
    else
        echo "[FAIL] $description (expected $expected, got $response)"
        FAIL=$((FAIL+1))
    fi
}

# Health Check
check "Health Check" "GET" "$BASE_URL/health" "" "200"

# Sessions
check "List sessions" "GET" "$BASE_URL/sessions" "" "200"

# Purchase (positive)
check "Purchase ticket (valid)" "POST" "$BASE_URL/tickets/purchase" \
    '{"session_id":1,"user_id":1}' "201"

# Purchase (negative - no session_id)
check "Purchase ticket (no session_id)" "POST" "$BASE_URL/tickets/purchase" \
    '{"user_id":1}' "400"

# Refund (positive) — используем ID билета, созданного выше (теоретически 4, но может быть другим)
check "Refund ticket" "POST" "$BASE_URL/tickets/4/refund" "" "200"

# User tickets
check "User tickets" "GET" "$BASE_URL/users/1/tickets" "" "200"

# Admin: List halls
check "List halls" "GET" "$BASE_URL/admin/halls" "" "200"

# Admin: Create hall
check "Create hall" "POST" "$BASE_URL/admin/halls" \
    '{"name":"Smoke Hall","capacity":30,"base_price":400.00}' "201"

# Admin: List movies
check "List movies" "GET" "$BASE_URL/admin/movies" "" "200"

echo "-----------------------"
echo "Total: $((PASS+FAIL)), PASS: $PASS, FAIL: $FAIL"
