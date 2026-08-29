#!/usr/bin/env bash
set -e

echo "=== Phase 5 Tactical Router Validation ==="

echo "1. Ensuring all containers are up..."
docker compose up -d

echo "2. Pinging Gateway B from Gateway A (Through Router)..."
if docker compose exec -T gateway-a ping -c 1 -W 2 gateway-b > /dev/null 2>&1; then
    echo "✅ PASSED: Gateway A can reach Gateway B."
else
    echo "❌ FAILED: Gateway A cannot reach Gateway B."
    exit 1
fi

echo "3. Stopping netem-router to prove isolation..."
docker compose stop netem-router

echo "4. Pinging Gateway B from Gateway A (Without Router)..."
if docker compose exec -T gateway-a ping -c 1 -W 2 gateway-b > /dev/null 2>&1; then
    echo "❌ FAILED: Gateway A can still reach Gateway B! The networks are not isolated."
    docker compose start netem-router
    exit 1
else
    echo "✅ PASSED: Gateway A cannot reach Gateway B when the router is down."
fi

echo "5. Restoring netem-router..."
docker compose start netem-router
sleep 2

echo "6. Pinging Gateway B from Gateway A (Router Restored)..."
if docker compose exec -T gateway-a ping -c 1 -W 2 gateway-b > /dev/null 2>&1; then
    echo "✅ PASSED: Gateway A can reach Gateway B again."
else
    echo "❌ FAILED: Gateway A cannot reach Gateway B after router restored."
    exit 1
fi

echo "=== Validation Complete! Router is functioning as the exclusive bridge. ==="
