"""Tests for benchmark_runner.report - CSV and chart generation."""
import csv
import os
import pandas as pd
import pytest

from benchmark_runner.report import ReportGenerator

@pytest.fixture()
def sample_results():
    return [
        {"crypto": "X25519", "profile": "stable", "avg_rtt_ms": 0.1, "mean_latency_ms": 10.0},
        {"crypto": "X25519MLKEM768", "profile": "adverse", "avg_rtt_ms": 100.0, "mean_latency_ms": 150.0},
    ]

@pytest.fixture()
def dummy_raw_latencies():
    return [
        {"crypto": "X25519", "profile": "stable", "iteration": 1, "latency": pd.Series([10.0, 11.0, 9.0])},
        {"crypto": "X25519MLKEM768", "profile": "adverse", "iteration": 1, "latency": pd.Series([140.0, 160.0, 150.0])},
    ]

class TestReportGeneratorGenerate:
    def test_writes_csv_with_correct_headers(self, sample_results, dummy_raw_latencies, tmp_path):
        gen = ReportGenerator()
        gen.generate(sample_results, dummy_raw_latencies, str(tmp_path))
        csv_path = tmp_path / "benchmark_report.csv"
        assert csv_path.exists()
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            assert "crypto" in reader.fieldnames
            assert "profile" in reader.fieldnames

    def test_csv_contains_all_result_rows(self, sample_results, dummy_raw_latencies, tmp_path):
        gen = ReportGenerator()
        gen.generate(sample_results, dummy_raw_latencies, str(tmp_path))
        csv_path = tmp_path / "benchmark_report.csv"
        with open(csv_path, "r") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2

    def test_generates_latency_summary_chart(self, sample_results, dummy_raw_latencies, tmp_path):
        gen = ReportGenerator()
        gen.generate(sample_results, dummy_raw_latencies, str(tmp_path))
        assert (tmp_path / "boxplot_latency_comparison.png").exists()

    def test_generates_latency_cdf_charts(self, sample_results, dummy_raw_latencies, tmp_path):
        gen = ReportGenerator()
        gen.generate(sample_results, dummy_raw_latencies, str(tmp_path))
        assert (tmp_path / "cdf_overlay.png").exists()

    def test_empty_results_produces_no_csv(self, tmp_path):
        gen = ReportGenerator()
        gen.generate([], [], str(tmp_path))
        assert not (tmp_path / "benchmark_report.csv").exists()

    def test_output_dir_is_created_if_missing(self, sample_results, dummy_raw_latencies, tmp_path):
        nested_dir = tmp_path / "deep" / "nested" / "evidence"
        gen = ReportGenerator()
        gen.generate(sample_results, dummy_raw_latencies, str(nested_dir))
        assert (nested_dir / "benchmark_report.csv").exists()
