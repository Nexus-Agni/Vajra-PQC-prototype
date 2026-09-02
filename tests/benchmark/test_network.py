"""Tests for benchmark_runner.network — network profile toggling and RTT probing."""
from unittest.mock import MagicMock

import pytest

from benchmark_runner.network import NetworkController


# ── Helpers ─────────────────────────────────────────────────────────────


def _make_exec(container_name="test-router-1", ping_output=""):
    """Build a mock exec_fn that resolves container names and returns ping output.

    The first call to exec_fn resolves the container name (docker ps),
    subsequent calls are the actual tc / ping commands.
    """
    mock = MagicMock()

    def side_effect(cmd):
        if "docker ps" in cmd:
            return container_name
        return ping_output

    mock.side_effect = side_effect
    return mock


# ── Tests ───────────────────────────────────────────────────────────────


class TestNetworkControllerToggleProfile:
    """Seam: NetworkController.toggle_profile(profile) builds correct tc commands."""

    def test_adverse_profile_applies_delay_and_loss_to_both_interfaces(self):
        mock_exec = _make_exec(container_name="my-router-1")
        controller = NetworkController(exec_fn=mock_exec)

        controller.toggle_profile("adverse")

        # 1 call for container resolution + 2 calls for tc (eth0, eth1)
        tc_calls = [
            c for c in mock_exec.call_args_list
            if "docker ps" not in c[0][0]
        ]
        assert len(tc_calls) == 2

        eth0_cmd = tc_calls[0][0][0]
        eth1_cmd = tc_calls[1][0][0]

        assert "netem delay 50ms 10ms" in eth0_cmd
        assert "loss 3%" in eth0_cmd
        assert "rate 5mbit" in eth0_cmd
        assert "eth0" in eth0_cmd
        assert "my-router-1" in eth0_cmd  # resolved container name

        assert "netem delay 50ms 10ms" in eth1_cmd
        assert "loss 3%" in eth1_cmd
        assert "rate 5mbit" in eth1_cmd
        assert "eth1" in eth1_cmd

    def test_stable_profile_removes_tc_rules(self):
        mock_exec = _make_exec(container_name="my-router-1")
        controller = NetworkController(exec_fn=mock_exec)

        controller.toggle_profile("stable")

        tc_calls = [
            c for c in mock_exec.call_args_list
            if "docker ps" not in c[0][0]
        ]
        assert len(tc_calls) == 2

        eth0_cmd = tc_calls[0][0][0]
        eth1_cmd = tc_calls[1][0][0]

        assert "del" in eth0_cmd
        assert "eth0" in eth0_cmd
        assert "del" in eth1_cmd
        assert "eth1" in eth1_cmd

    def test_toggle_profile_returns_profile_name(self):
        mock_exec = _make_exec()
        controller = NetworkController(exec_fn=mock_exec)

        assert controller.toggle_profile("adverse") == "adverse"
        assert controller.toggle_profile("stable") == "stable"


class TestNetworkControllerProbeRtt:
    """Seam: NetworkController.probe_rtt() runs ping via docker exec into gateway-a."""

    def test_parses_linux_ping_output_for_average_rtt(self):
        ping_output = (
            "PING 172.26.0.2 (172.26.0.2) 56(84) bytes of data.\n"
            "64 bytes from 172.26.0.2: icmp_seq=1 ttl=64 time=0.123 ms\n"
            "64 bytes from 172.26.0.2: icmp_seq=2 ttl=64 time=0.145 ms\n"
            "64 bytes from 172.26.0.2: icmp_seq=3 ttl=64 time=0.132 ms\n"
            "\n"
            "--- 172.26.0.2 ping statistics ---\n"
            "3 packets transmitted, 3 received, 0% packet loss, time 2003ms\n"
            "rtt min/avg/max/mdev = 0.123/0.133/0.145/0.009 ms\n"
        )
        mock_exec = _make_exec(
            container_name="gw-a-container-1",
            ping_output=ping_output,
        )
        controller = NetworkController(exec_fn=mock_exec)

        avg_rtt = controller.probe_rtt()
        assert avg_rtt == pytest.approx(0.133, abs=0.001)

    def test_returns_zero_when_ping_output_unparseable(self):
        mock_exec = _make_exec(ping_output="Request timed out")
        controller = NetworkController(exec_fn=mock_exec)

        assert controller.probe_rtt() == 0.0

    def test_probe_rtt_docker_execs_into_gateway_a_container(self):
        mock_exec = _make_exec(
            container_name="resolved-gw-a",
            ping_output="rtt min/avg/max/mdev = 1.0/2.0/3.0/0.5 ms",
        )
        controller = NetworkController(
            exec_fn=mock_exec, target_ip="172.26.0.2"
        )
        controller.probe_rtt()

        # Find the ping command (not the docker ps resolution call)
        ping_calls = [
            c for c in mock_exec.call_args_list
            if "ping" in c[0][0]
        ]
        assert len(ping_calls) == 1

        ping_cmd = ping_calls[0][0][0]
        assert "docker exec" in ping_cmd
        assert "resolved-gw-a" in ping_cmd  # resolved container name
        assert "172.26.0.2" in ping_cmd


class TestNetworkControllerContainerResolution:
    """Container name resolution via Compose labels."""

    def test_resolves_via_docker_ps_with_compose_labels(self):
        mock_exec = _make_exec(container_name="proto-netem-router-1")
        controller = NetworkController(exec_fn=mock_exec)

        controller.toggle_profile("stable")

        # First call should be the docker ps resolution
        first_call = mock_exec.call_args_list[0][0][0]
        assert "docker ps" in first_call
        assert "com.docker.compose.project=" in first_call
        assert "com.docker.compose.service=netem-router" in first_call

    def test_falls_back_to_service_name_on_empty_response(self):
        mock_exec = MagicMock(return_value="")
        controller = NetworkController(exec_fn=mock_exec)

        # Should not crash — falls back gracefully
        controller.toggle_profile("stable")
        assert mock_exec.call_count > 0
