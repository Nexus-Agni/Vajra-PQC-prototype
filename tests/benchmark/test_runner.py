"""Tests for benchmark_runner.runner — end-to-end orchestration."""
import json
import os
from unittest.mock import MagicMock, patch, call

import pytest

from benchmark_runner.runner import BenchmarkRunner


# ── Fixtures ────────────────────────────────────────────────────────────


def _write_telemetry_files(a_path, b_path, count=10):
    """Write realistic telemetry files with `count` matched transactions."""
    a_records = []
    b_records = []
    base_ns = 1_000_000_000_000

    for i in range(count):
        tx_id = f"tx-{i:04d}"
        t_received = base_ns + i * 100_000_000
        t_extracted = t_received + 3_000_000
        t_signed = t_extracted + 2_000_000
        t_acked = t_signed + 15_000_000
        t_received_b = t_signed + 5_000_000
        t_verified_b = t_received_b + 1_000_000
        t_ingested_b = t_verified_b + 8_000_000

        a_records.append({
            "transaction_id": tx_id,
            "state": "acked",
            "telemetry": {
                "t_received": t_received,
                "t_extracted": t_extracted,
                "t_signed": t_signed,
                "t_acked": t_acked,
                "retry_count": 1,
            },
        })
        b_records.append({
            "transaction_id": tx_id,
            "state": "ACKED",
            "telemetry": {
                "t_received_b": t_received_b,
                "t_verified_b": t_verified_b,
                "t_ingested_b": t_ingested_b,
            },
        })

    for path, records in [(a_path, a_records), (b_path, b_records)]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")


@pytest.fixture()
def runner_env(tmp_path):
    """Set up a BenchmarkRunner with all external deps mocked.

    The mock exec_fn also simulates event injection by writing
    telemetry files, since the real gateways aren't running.
    """
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()

    a_path = str(evidence_dir / "telemetry_a.jsonl")
    b_path = str(evidence_dir / "telemetry_b.jsonl")

    def mock_exec(cmd):
        """Simulate external commands. When 'misp_publisher_mock' is called,
        write fresh telemetry files to simulate gateway processing."""
        if "misp_publisher_mock" in cmd:
            _write_telemetry_files(a_path, b_path, count=10)
        return "rtt min/avg/max/mdev = 0.1/0.2/0.3/0.05 ms"

    runner = BenchmarkRunner(
        evidence_dir=str(evidence_dir),
        telemetry_a_path=a_path,
        telemetry_b_path=b_path,
        exec_fn=mock_exec,
        event_count=10,
        wait_seconds=0,  # No waiting in tests
    )
    return runner, evidence_dir, mock_exec


# ── Tests ───────────────────────────────────────────────────────────────


class TestBenchmarkRunnerRun:
    """Seam: BenchmarkRunner.run() orchestrates full benchmark campaign."""

    def test_produces_benchmark_csv_in_evidence_dir(self, runner_env):
        runner, evidence_dir, _ = runner_env
        runner.run()

        csv_path = evidence_dir / "benchmark_report.csv"
        assert csv_path.exists()

    def test_produces_latency_summary_chart(self, runner_env):
        runner, evidence_dir, _ = runner_env
        runner.run()

        chart_path = evidence_dir / "latency_summary.png"
        assert chart_path.exists()

    def test_iterates_over_both_crypto_groups(self, runner_env):
        runner, evidence_dir, _ = runner_env
        runner.run()

        import csv as csv_mod
        csv_path = evidence_dir / "benchmark_report.csv"
        with open(csv_path, "r") as f:
            rows = list(csv_mod.DictReader(f))

        cryptos = {r["crypto"] for r in rows}
        assert "X25519" in cryptos
        assert "X25519MLKEM768" in cryptos

    def test_iterates_over_both_network_profiles(self, runner_env):
        runner, evidence_dir, _ = runner_env
        runner.run()

        import csv as csv_mod
        csv_path = evidence_dir / "benchmark_report.csv"
        with open(csv_path, "r") as f:
            rows = list(csv_mod.DictReader(f))

        profiles = {r["profile"] for r in rows}
        assert "stable" in profiles
        assert "adverse" in profiles

    def test_records_actual_rtt_in_results(self, runner_env):
        runner, evidence_dir, _ = runner_env
        runner.run()

        import csv as csv_mod
        csv_path = evidence_dir / "benchmark_report.csv"
        with open(csv_path, "r") as f:
            rows = list(csv_mod.DictReader(f))

        for row in rows:
            assert float(row["avg_rtt_ms"]) >= 0.0

    def test_returns_four_results_for_two_crypto_two_profiles(self, runner_env):
        runner, _, _ = runner_env
        results = runner.run()

        assert len(results) == 4
        combos = {(r["crypto"], r["profile"]) for r in results}
        assert ("X25519", "stable") in combos
        assert ("X25519", "adverse") in combos
        assert ("X25519MLKEM768", "stable") in combos
        assert ("X25519MLKEM768", "adverse") in combos
