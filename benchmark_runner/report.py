"""Report generation: CSV summaries and matplotlib charts."""
from __future__ import annotations

import logging
import os
from typing import Dict, Any, List

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Write benchmark results to CSV and generate summary charts.

    All outputs are written to the evidence directory so that
    ``results/phase5/evidence/`` is the single source of truth.
    """

    def generate(
        self,
        results: List[Dict[str, Any]],
        output_dir: str,
    ) -> None:
        """Write benchmark_report.csv and latency_summary.png.

        Args:
            results: List of per-run metric dicts from MetricsCalculator.
            output_dir: Directory to write outputs into (created if needed).
        """
        os.makedirs(output_dir, exist_ok=True)

        df = pd.DataFrame(results)
        csv_path = os.path.join(output_dir, "benchmark_report.csv")
        df.to_csv(csv_path, index=False)
        logger.info("Wrote benchmark CSV to %s", csv_path)

        if not results:
            return

        self._plot_latency_summary(df, output_dir)

    # ── chart helpers ───────────────────────────────────────────────

    @staticmethod
    def _plot_latency_summary(df: pd.DataFrame, output_dir: str) -> None:
        """Bar chart comparing mean and P95 latency across configurations."""
        fig, ax = plt.subplots(figsize=(10, 6))
        df = df.copy()
        df["label"] = df["crypto"] + "_" + df["profile"]
        df.plot(
            x="label",
            y=["mean_latency_ms", "p95_latency_ms"],
            kind="bar",
            ax=ax,
        )
        ax.set_title("Latency by Crypto and Network Profile")
        ax.set_ylabel("Latency (ms)")
        ax.tick_params(axis="x", rotation=45)
        fig.tight_layout()

        chart_path = os.path.join(output_dir, "latency_summary.png")
        fig.savefig(chart_path)
        plt.close(fig)
        logger.info("Wrote latency summary chart to %s", chart_path)

    @staticmethod
    def plot_cdf(
        latency_series: pd.Series,
        crypto: str,
        profile: str,
        output_dir: str,
    ) -> None:
        """CDF of end-to-end latency for a single configuration.

        Called from the runner with the raw per-transaction latency data,
        since the ReportGenerator only receives aggregated metrics.
        """
        fig, ax = plt.subplots()
        latency_series.hist(cumulative=True, density=True, bins=50, ax=ax)
        ax.set_title(f"CDF of End-to-End Latency ({crypto} - {profile})")
        ax.set_xlabel("Latency (ms)")
        ax.set_ylabel("CDF")

        chart_path = os.path.join(
            output_dir, f"latency_cdf_{crypto}_{profile}.png"
        )
        fig.savefig(chart_path)
        plt.close(fig)
        logger.info("Wrote CDF chart to %s", chart_path)
