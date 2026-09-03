"""Tests for benchmark_runner.metrics — latency and overhead calculations."""
import pandas as pd
import pytest

from benchmark_runner.metrics import MetricsCalculator


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def merged_df():
    """A realistic merged DataFrame as TelemetryCollector.collect() would return.

    Two transactions with known nanosecond timestamps so we can assert
    exact millisecond results without tautological recomputation.

    tx-001:
        t_received    = 0 ns
        t_extracted   = 2_000_000 ns  →  extraction = 2.0 ms
        t_signed      = 5_000_000 ns  →  signing    = 3.0 ms
        t_ingested_b  = 18_000_000 ns →  total      = 18.0 ms
        t_verified_b  = 11_000_000 ns →  net+verify  = 6.0 ms
        retry_count   = 1

    tx-002:
        t_received    = 100_000_000 ns
        t_extracted   = 106_000_000 ns  →  extraction = 6.0 ms
        t_signed      = 110_000_000 ns  →  signing    = 4.0 ms
        t_ingested_b  = 140_000_000 ns  →  total      = 40.0 ms
        t_verified_b  = 120_000_000 ns  →  net+verify  = 10.0 ms
        retry_count   = 3
    """
    return pd.DataFrame([
        {
            "tx_id": "tx-001",
            "t_received": 0,
            "t_extracted": 2_000_000,
            "t_signed": 5_000_000,
            "t_acked": 20_000_000,
            "retry_count": 1,
            "t_received_b": 10_000_000,
            "t_verified_b": 11_000_000,
            "t_ingested_b": 18_000_000,
        },
        {
            "tx_id": "tx-002",
            "t_received": 100_000_000,
            "t_extracted": 106_000_000,
            "t_signed": 110_000_000,
            "t_acked": 145_000_000,
            "retry_count": 3,
            "t_received_b": 115_000_000,
            "t_verified_b": 120_000_000,
            "t_ingested_b": 140_000_000,
        },
    ])


@pytest.fixture()
def single_row_df():
    """A single-row DataFrame for percentile edge cases."""
    return pd.DataFrame([
        {
            "tx_id": "tx-solo",
            "t_received": 0,
            "t_extracted": 1_000_000,
            "t_signed": 2_000_000,
            "t_acked": 10_000_000,
            "retry_count": 0,
            "t_received_b": 5_000_000,
            "t_verified_b": 6_000_000,
            "t_ingested_b": 8_000_000,
        },
    ])


# ── Tests ───────────────────────────────────────────────────────────────


class TestMetricsCalculatorCompute:
    """Seam: MetricsCalculator.compute(df) → metrics dict."""

    def test_mean_latency_is_arithmetic_average(self, merged_df):
        calc = MetricsCalculator()
        metrics = calc.compute(merged_df)
        # total latency: tx-001 = 18.0 ms, tx-002 = 40.0 ms → mean = 29.0 ms
        assert metrics["mean_latency_ms"] == pytest.approx(29.0, abs=0.01)

    def test_p95_is_near_max_for_two_samples(self, merged_df):
        calc = MetricsCalculator()
        metrics = calc.compute(merged_df)
        # With only 2 samples, p95 interpolates between 18.0 and 40.0
        assert 18.0 <= metrics["p95_latency_ms"] <= 40.0

    def test_p99_is_near_max_for_two_samples(self, merged_df):
        calc = MetricsCalculator()
        metrics = calc.compute(merged_df)
        assert 18.0 <= metrics["p99_latency_ms"] <= 40.0

    def test_mean_retries_averaged_correctly(self, merged_df):
        calc = MetricsCalculator()
        metrics = calc.compute(merged_df)
        # retry_count: 1 and 3 → mean = 2.0
        assert metrics["mean_retries"] == pytest.approx(2.0, abs=0.01)

    def test_count_reflects_row_count(self, merged_df):
        calc = MetricsCalculator()
        metrics = calc.compute(merged_df)
        assert metrics["count"] == 2

    def test_single_row_produces_deterministic_percentiles(self, single_row_df):
        calc = MetricsCalculator()
        metrics = calc.compute(single_row_df)
        # With a single data point (8.0 ms total), all percentiles equal the value
        assert metrics["mean_latency_ms"] == pytest.approx(8.0, abs=0.01)
        assert metrics["p95_latency_ms"] == pytest.approx(8.0, abs=0.01)
        assert metrics["p99_latency_ms"] == pytest.approx(8.0, abs=0.01)

    def test_empty_dataframe_returns_none(self):
        calc = MetricsCalculator()
        result = calc.compute(pd.DataFrame())
        assert result is None

    def test_breakdown_latencies_included(self, merged_df):
        calc = MetricsCalculator()
        metrics = calc.compute(merged_df)
        # extraction: tx-001 = 2.0, tx-002 = 6.0 → mean = 4.0
        assert metrics["mean_extraction_ms"] == pytest.approx(4.0, abs=0.01)
        # signing: tx-001 = 3.0, tx-002 = 4.0 → mean = 3.5
        assert metrics["mean_signing_ms"] == pytest.approx(3.5, abs=0.01)
        # network_and_verify: tx-001 = 6.0, tx-002 = 10.0 → mean = 8.0
        assert metrics["mean_network_verify_ms"] == pytest.approx(8.0, abs=0.01)
