#!/usr/bin/env bash
set -e

echo "=== Phase 5 Network Isolation Validation ==="

# Test if Gateway A can ping Gateway B
echo "Testing if Gateway A can reach Gateway B (Expected: FAILURE)"
if docker compose exec -T gateway-a ping -c 1 -W 2 gateway-b > /dev/null 2>&1; then
    echo "❌ FAILED: Gateway A can reach Gateway B directly. They are not isolated!"
    exit 1
else
    echo "✅ PASSED: Gateway A cannot reach Gateway B directly."
fi

# Test if Gateway B can ping Gateway A
echo "Testing if Gateway B can reach Gateway A (Expected: FAILURE)"
if docker compose exec -T gateway-b ping -c 1 -W 2 gateway-a > /dev/null 2>&1; then
    echo "❌ FAILED: Gateway B can reach Gateway A directly. They are not isolated!"
    exit 1
else
    echo "✅ PASSED: Gateway B cannot reach Gateway A directly."
fi

echo "=== Startup and Health Validation ==="
echo "Testing if containers are running and healthy..."

declare -a services=("misp" "opencti" "gateway-a" "gateway-b" "qstie-ca-bootstrap")
for service in "${services[@]}"; do
    state=$(docker compose ps -q $service | xargs docker inspect -f '{{.State.Status}}')
    if [ "$state" != "running" ]; then
        echo "❌ FAILED: Service $service is not running (State: $state)"
        exit 1
    else
        echo "✅ PASSED: Service $service is running."
    fi
done

echo "✅ All Phase 5 foundation validations passed successfully."
