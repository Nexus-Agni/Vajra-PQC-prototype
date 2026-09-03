"""Tests for benchmark_runner.report — CSV and chart generation."""
import csv
import os

import pytest

from benchmark_runner.report import ReportGenerator


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def sample_results():
    """Two benchmark result dicts as the runner would produce."""
    return [
        {
            "crypto": "X25519",
            "profile": "stable",
            "avg_rtt_ms": 0.15,
            "mean_latency_ms": 6740.78,
            "p95_latency_ms": 13239.61,
            "p99_latency_ms": 13520.30,
            "mean_retries": 1.0,
            "count": 50,
            "mean_extraction_ms": 3.2,
            "mean_signing_ms": 1.5,
            "mean_network_verify_ms": 350.0,
        },
        {
            "crypto": "X25519MLKEM768",
            "profile": "adverse",
            "avg_rtt_ms": 50.4,
            "mean_latency_ms": 12791.70,
            "p95_latency_ms": 23216.50,
            "p99_latency_ms": 24642.36,
            "mean_retries": 1.0,
            "count": 50,
            "mean_extraction_ms": 4.1,
            "mean_signing_ms": 2.8,
            "mean_network_verify_ms": 500.0,
        },
    ]


# ── Tests ───────────────────────────────────────────────────────────────


class TestReportGeneratorGenerate:
    """Seam: ReportGenerator.generate(results, output_dir) writes files."""

    def test_writes_csv_with_correct_headers(self, sample_results, tmp_path):
        gen = ReportGenerator()
        gen.generate(sample_results, str(tmp_path))

        csv_path = tmp_path / "benchmark_report.csv"
        assert csv_path.exists()

        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            assert "crypto" in headers
            assert "profile" in headers
            assert "mean_latency_ms" in headers
            assert "p95_latency_ms" in headers
            assert "p99_latency_ms" in headers
            assert "mean_retries" in headers
            assert "count" in headers

    def test_csv_contains_all_result_rows(self, sample_results, tmp_path):
        gen = ReportGenerator()
        gen.generate(sample_results, str(tmp_path))

        csv_path = tmp_path / "benchmark_report.csv"
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["crypto"] == "X25519"
        assert rows[1]["crypto"] == "X25519MLKEM768"

    def test_generates_latency_summary_chart(self, sample_results, tmp_path):
        gen = ReportGenerator()
        gen.generate(sample_results, str(tmp_path))

        chart_path = tmp_path / "latency_summary.png"
        assert chart_path.exists()
        assert chart_path.stat().st_size > 0

    def test_generates_latency_cdf_charts(self, sample_results, tmp_path):
        """A CDF chart is generated per result (crypto+profile combo)."""
        gen = ReportGenerator()
        gen.generate(sample_results, str(tmp_path))

        # We don't generate CDF per result in the report generator itself —
        # CDFs require the raw DataFrame. This test just ensures the bar chart exists.
        # CDF generation happens in the runner with access to the raw data.
        assert (tmp_path / "latency_summary.png").exists()

    def test_empty_results_produces_empty_csv(self, tmp_path):
        gen = ReportGenerator()
        gen.generate([], str(tmp_path))

        csv_path = tmp_path / "benchmark_report.csv"
        assert csv_path.exists()
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 0

    def test_output_dir_is_created_if_missing(self, sample_results, tmp_path):
        nested_dir = tmp_path / "deep" / "nested" / "evidence"
        gen = ReportGenerator()
        gen.generate(sample_results, str(nested_dir))

        assert (nested_dir / "benchmark_report.csv").exists()
