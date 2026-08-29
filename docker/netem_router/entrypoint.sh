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
    # Apply to eth0 (towards tactical_a_net)
    tc qdisc add dev eth0 root netem delay 50ms 10ms loss 5% || true
    # Apply to eth1 (towards tactical_b_net)
    tc qdisc add dev eth1 root netem delay 50ms 10ms loss 5% || true
else
    echo "Applying stable network conditions (no tc rules)."
fi

echo "Router is running. Waiting for traffic..."
exec tail -f /dev/null
