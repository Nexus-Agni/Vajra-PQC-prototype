#!/bin/bash
set -e

echo "Starting netem-router..."

# Note: IP forwarding is enabled via sysctls in docker-compose.yaml
# We still run it here just in case the container has privileges but sysctls wasn't passed
sysctl -w net.ipv4.ip_forward=1 || true

# Forwarding rule
iptables -P FORWARD ACCEPT

# By default, we apply a 'stable' profile (no delay)
# If the environment variable PROFILE=adverse, we apply netem delays.
if [ "$PROFILE" = "adverse" ]; then
    echo "Applying adverse network conditions..."
    for dev in eth0 eth1; do
        tc qdisc add dev $dev root netem delay 50ms 10ms loss 3% rate 5mbit || true
    done
else
    echo "Applying stable network conditions (no tc rules)."
fi

echo "Router is running. Waiting for traffic..."
exec tail -f /dev/null
