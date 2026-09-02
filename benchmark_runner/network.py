"""Network control: toggle netem profiles and probe RTT via Docker containers."""
from __future__ import annotations

import logging
import subprocess
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Type alias for the command execution function (system boundary).
# Default implementation shells out via subprocess; tests inject a mock.
ExecFn = Callable[[str], str]

# Compose project name used for container label lookups.
COMPOSE_PROJECT = "prototype-implementation-main"


def _default_exec(cmd: str) -> str:
    """Run a shell command and return combined stdout+stderr."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr).strip()


class NetworkController:
    """Toggle netem-router between stable/adverse and probe actual RTT.

    All operations run inside Docker containers via ``docker exec``.
    The ``exec_fn`` parameter is the system-boundary seam: in production
    it runs shell commands against the Docker socket; in tests it's
    replaced with a mock.

    Adverse profile: 50ms delay with 10ms jitter, 3% loss, and 5mbit
    bandwidth limit per interface. Matches the ticket specification of
    "50ms 10ms loss 3% rate 5mbit".
    """

    ADVERSE_DELAY = "50ms 10ms"
    ADVERSE_LOSS = "3%"
    ADVERSE_RATE = "5mbit"

    def __init__(
        self,
        exec_fn: ExecFn = _default_exec,
        router_service: str = "netem-router",
        gateway_a_service: str = "gateway-a",
        target_ip: str = "172.26.0.2",
        ping_count: int = 5,
    ) -> None:
        self._exec = exec_fn
        self._router_service = router_service
        self._gw_a_service = gateway_a_service
        self._target_ip = target_ip
        self._ping_count = ping_count

    # ── public API ──────────────────────────────────────────────────

    def toggle_profile(self, profile: str) -> str:
        """Apply the named network profile to the netem-router.

        Args:
            profile: ``"adverse"`` or ``"stable"``.

        Returns:
            The profile name that was applied.
        """
        if profile == "adverse":
            self._apply_adverse()
        else:
            self._clear_rules()

        logger.info("Network profile set to '%s'", profile)
        return profile

    def probe_rtt(self) -> float:
        """Ping Gateway B from Gateway A through the tactical network.

        Runs ``docker exec`` into the gateway-a container and pings the
        Gateway B IP (172.26.0.2) across the netem-router, so the measured
        RTT reflects actual network impairment.

        Returns 0.0 if the ping output cannot be parsed (e.g. timeout).
        """
        gw_a = self._resolve_container(self._gw_a_service)
        cmd = (
            f"docker exec {gw_a} ping -c {self._ping_count} {self._target_ip}"
        )
        output = self._exec(cmd)
        return self._parse_ping_avg(output)

    # ── internals ───────────────────────────────────────────────────

    def _resolve_container(self, service: str) -> str:
        """Resolve a Compose service name to the running container name.

        Uses ``docker ps`` with Compose project/service label filters,
        matching the original benchmark runner's ``get_container_name()``.
        Falls back to the service name if lookup fails.
        """
        cmd = (
            f"docker ps "
            f"--filter label=com.docker.compose.project={COMPOSE_PROJECT} "
            f"--filter label=com.docker.compose.service={service} "
            f"--format '{{{{.Names}}}}'"
        )
        result = self._exec(cmd).strip().strip("'").split("\n")[0]
        if not result:
            logger.warning(
                "Could not resolve container for service '%s', "
                "falling back to service name",
                service,
            )
            return service
        return result

    def _apply_adverse(self) -> None:
        router = self._resolve_container(self._router_service)
        for iface in ("eth0", "eth1"):
            # Adverse profile command:
            # tc qdisc add dev ethX root netem delay 50ms 10ms loss 3% rate 5mbit
            cmd = (
                f"docker exec {router} bash -c "
                f"\"tc qdisc add dev {iface} root netem "
                f"delay {self.ADVERSE_DELAY} loss {self.ADVERSE_LOSS} rate {self.ADVERSE_RATE} "
                f"2>/dev/null || tc qdisc change dev {iface} root netem "
                f"delay {self.ADVERSE_DELAY} loss {self.ADVERSE_LOSS} rate {self.ADVERSE_RATE}\""
            )
            self._exec(cmd)

    def _clear_rules(self) -> None:
        router = self._resolve_container(self._router_service)
        for iface in ("eth0", "eth1"):
            # Stable profile command (clears existing rules):
            # tc qdisc del dev ethX root
            cmd = (
                f"docker exec {router} bash -c "
                f"\"tc qdisc del dev {iface} root 2>/dev/null || true\""
            )
            self._exec(cmd)

    @staticmethod
    def _parse_ping_avg(output: str) -> float:
        """Extract average RTT from Linux ping rtt summary line."""
        for line in output.splitlines():
            if "rtt min/avg/max/mdev" in line:
                try:
                    parts = line.split("=")[1].strip().split("/")
                    return float(parts[1])
                except (IndexError, ValueError):
                    pass
        return 0.0
