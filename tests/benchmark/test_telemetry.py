"""Tests for benchmark_runner.telemetry — JSONL ingestion and merge."""
import json
import os
import tempfile

import pandas as pd
import pytest

from benchmark_runner.telemetry import TelemetryCollector


# ── Fixtures ────────────────────────────────────────────────────────────

def _write_jsonl(path, records):
    """Helper: write a list of dicts as newline-delimited JSON."""
    with open(path, "w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


@pytest.fixture()
def telemetry_dir(tmp_path):
    """Create a temp dir with realistic telemetry_a.jsonl and telemetry_b.jsonl."""
    a_records = [
        {
            "transaction_id": "tx-001",
            "state": "acked",
            "telemetry": {
                "t_received": 1000000000,
                "t_extracted": 1003000000,
                "t_signed": 1005000000,
                "t_acked": 1020000000,
                "retry_count": 1,
            },
        },
        {
            "transaction_id": "tx-002",
            "state": "acked",
            "telemetry": {
                "t_received": 2000000000,
                "t_extracted": 2004000000,
                "t_signed": 2006000000,
                "t_acked": 2030000000,
                "retry_count": 2,
            },
        },
        # This one is not ACKED — should be excluded.
        {
            "transaction_id": "tx-003",
            "state": "sending",
            "telemetry": {
                "t_received": 3000000000,
                "t_extracted": 3001000000,
                "t_signed": 3002000000,
            },
        },
    ]

    b_records = [
        {
            "transaction_id": "tx-001",
            "state": "ACKED",
            "telemetry": {
                "t_received_b": 1010000000,
                "t_verified_b": 1011000000,
                "t_ingested_b": 1018000000,
            },
        },
        {
            "transaction_id": "tx-002",
            "state": "ACKED",
            "telemetry": {
                "t_received_b": 2010000000,
                "t_verified_b": 2012000000,
                "t_ingested_b": 2025000000,
            },
        },
        # tx-004 exists only in B — no matching A record, should be dropped.
        {
            "transaction_id": "tx-004",
            "state": "ACKED",
            "telemetry": {
                "t_received_b": 4000000000,
                "t_verified_b": 4001000000,
                "t_ingested_b": 4002000000,
            },
        },
    ]

    _write_jsonl(tmp_path / "telemetry_a.jsonl", a_records)
    _write_jsonl(tmp_path / "telemetry_b.jsonl", b_records)
    return tmp_path


@pytest.fixture()
def empty_dir(tmp_path):
    """A directory with no telemetry files."""
    return tmp_path


# ── Tests ───────────────────────────────────────────────────────────────


class TestTelemetryCollectorCollect:
    """Seam: TelemetryCollector.collect() returns a merged DataFrame."""

    def test_merges_gateway_a_and_b_by_transaction_id(self, telemetry_dir):
        collector = TelemetryCollector(
            telemetry_a_path=str(telemetry_dir / "telemetry_a.jsonl"),
            telemetry_b_path=str(telemetry_dir / "telemetry_b.jsonl"),
        )
        df = collector.collect()

        # Only tx-001 and tx-002 should survive (tx-003 not acked, tx-004 no match)
        assert len(df) == 2
        assert set(df["tx_id"].tolist()) == {"tx-001", "tx-002"}

    def test_excludes_non_acked_gateway_a_events(self, telemetry_dir):
        collector = TelemetryCollector(
            telemetry_a_path=str(telemetry_dir / "telemetry_a.jsonl"),
            telemetry_b_path=str(telemetry_dir / "telemetry_b.jsonl"),
        )
        df = collector.collect()

        # tx-003 was "sending" — must not appear
        assert "tx-003" not in df["tx_id"].tolist()

    def test_includes_all_timestamp_columns(self, telemetry_dir):
        collector = TelemetryCollector(
            telemetry_a_path=str(telemetry_dir / "telemetry_a.jsonl"),
            telemetry_b_path=str(telemetry_dir / "telemetry_b.jsonl"),
        )
        df = collector.collect()

        expected_cols = {
            "tx_id",
            "t_received",
            "t_extracted",
            "t_signed",
            "t_acked",
            "retry_count",
            "t_received_b",
            "t_verified_b",
            "t_ingested_b",
        }
        assert expected_cols.issubset(set(df.columns))

    def test_preserves_timestamp_values(self, telemetry_dir):
        collector = TelemetryCollector(
            telemetry_a_path=str(telemetry_dir / "telemetry_a.jsonl"),
            telemetry_b_path=str(telemetry_dir / "telemetry_b.jsonl"),
        )
        df = collector.collect()

        row = df[df["tx_id"] == "tx-001"].iloc[0]
        assert row["t_received"] == 1000000000
        assert row["t_ingested_b"] == 1018000000

    def test_returns_empty_dataframe_when_no_telemetry_files(self, empty_dir):
        collector = TelemetryCollector(
            telemetry_a_path=str(empty_dir / "telemetry_a.jsonl"),
            telemetry_b_path=str(empty_dir / "telemetry_b.jsonl"),
        )
        df = collector.collect()
        assert len(df) == 0

    def test_handles_malformed_jsonl_lines_gracefully(self, telemetry_dir):
        """Corrupt lines in the JSONL should be skipped, not crash the collector."""
        a_path = telemetry_dir / "telemetry_a.jsonl"
        with open(a_path, "a") as f:
            f.write("not valid json\n")
            f.write("{incomplete\n")

        collector = TelemetryCollector(
            telemetry_a_path=str(a_path),
            telemetry_b_path=str(telemetry_dir / "telemetry_b.jsonl"),
        )
        df = collector.collect()
        # Should still have the 2 valid merged records
        assert len(df) == 2
