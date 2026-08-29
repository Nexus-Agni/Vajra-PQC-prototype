#!/usr/bin/env bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 [stable|adverse]"
    echo "Current profile is determined by environment variable or container state."
    exit 1
fi

PROFILE=$1

if [ "$PROFILE" != "stable" ] && [ "$PROFILE" != "adverse" ]; then
    echo "Error: Profile must be 'stable' or 'adverse'."
    exit 1
fi

echo "Switching netem-router to profile: $PROFILE"

if [ "$PROFILE" = "adverse" ]; then
    docker compose exec netem-router bash -c "tc qdisc add dev eth0 root netem delay 50ms 10ms loss 5% 2>/dev/null || tc qdisc change dev eth0 root netem delay 50ms 10ms loss 5%"
    docker compose exec netem-router bash -c "tc qdisc add dev eth1 root netem delay 50ms 10ms loss 5% 2>/dev/null || tc qdisc change dev eth1 root netem delay 50ms 10ms loss 5%"
    echo "✅ Adverse network conditions applied (50ms latency, 5% packet loss)."
else
    docker compose exec netem-router bash -c "tc qdisc del dev eth0 root 2>/dev/null || true"
    docker compose exec netem-router bash -c "tc qdisc del dev eth1 root 2>/dev/null || true"
    echo "✅ Stable network conditions applied (no tc rules)."
fi
