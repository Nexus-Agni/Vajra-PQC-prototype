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
        raw_latencies: List[Dict[str, Any]],
        output_dir: str,
    ) -> None:
        """Write benchmark_report.csv and generate academic plots.

        Args:
            results: List of per-run metric dicts from MetricsCalculator.
            raw_latencies: List of dicts with 'crypto', 'profile', 'iteration', 'latency' Series.
            output_dir: Directory to write outputs into (created if needed).
        """
        os.makedirs(output_dir, exist_ok=True)

        if not results:
            logger.warning("No results to report.")
            return

        df = pd.DataFrame(results)
        
        expected_columns = [
            "crypto", "profile", "iteration", "count", 
            "median_latency_ms", "mean_latency_ms", "std_dev_ms", 
            "ci_95_lower", "ci_95_upper", "p95_latency_ms", 
            "p99_latency_ms", "p999_latency_ms", "mean_retries",
            "avg_rtt_ms"
        ]
        
        # Add any missing columns just in case
        for col in expected_columns:
            if col not in df.columns:
                df[col] = pd.NA
                
        df_csv = df[expected_columns]
        
        csv_path = os.path.join(output_dir, "benchmark_report.csv")
        df_csv.to_csv(csv_path, index=False)
        logger.info("Wrote benchmark CSV to %s", csv_path)

        if not raw_latencies:
            return

        # Combine all latencies for plotting
        combined_df = []
        for rl in raw_latencies:
            series = rl["latency"]
            temp_df = pd.DataFrame({
                "latency_ms": series,
                "label": f'{rl["crypto"]}_{rl["profile"]}'
            })
            combined_df.append(temp_df)
            
        if not combined_df:
            return
            
        full_latency_df = pd.concat(combined_df, ignore_index=True)

        self._plot_boxplot(full_latency_df, output_dir)
        self._plot_cdfs(full_latency_df, output_dir)

    # ── chart helpers ───────────────────────────────────────────────

    @staticmethod
    def _plot_boxplot(df: pd.DataFrame, output_dir: str) -> None:
        """Box-and-whisker plot comparing all configurations side by side."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # df has 'latency_ms' and 'label'
        labels = df["label"].unique().tolist()
        data_to_plot = [df[df["label"] == label]["latency_ms"].dropna() for label in labels]
        
        ax.boxplot(data_to_plot, whis=(5.0, 95.0), sym='.')  # type: ignore
        ax.set_xticklabels(labels)
        
        ax.set_title("End-to-End Latency Distribution by Configuration")
        ax.set_ylabel("Latency (ms)")
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        fig.tight_layout()

        chart_path = os.path.join(output_dir, "boxplot_latency_comparison.png")
        fig.savefig(chart_path, dpi=300)
        plt.close(fig)
        logger.info("Wrote boxplot to %s", chart_path)

    @staticmethod
    def _plot_cdfs(df: pd.DataFrame, output_dir: str) -> None:
        """Generate individual and combined CDF plots."""
        labels = df["label"].unique().tolist()
        
        # Consistent color scheme and line styles
        colors = plt.get_cmap("tab10").colors  # type: ignore
        line_styles = ['-', '--', '-.', ':']
        
        # 1. Individual CDFs
        for i, label in enumerate(labels):
            fig, ax = plt.subplots(figsize=(8, 5))
            data = df[df["label"] == label]["latency_ms"].dropna()
            
            # Sort data for CDF
            x = data.sort_values()
            y = pd.Series(1, index=x.index).cumsum() / len(x)
            
            ax.plot(x, y, color=colors[i % len(colors)], linestyle='-')
            ax.set_title(f"CDF of End-to-End Latency ({label})")
            ax.set_xlabel("End-to-End Latency (ms)")
            ax.set_ylabel("CDF")
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.set_ylim((0.0, 1.05))
            fig.tight_layout()
            
            chart_path = os.path.join(output_dir, f"cdf_{label}.png")
            fig.savefig(chart_path, dpi=300)
            plt.close(fig)
            
        # 2. Combined CDF overlay
        fig, ax = plt.subplots(figsize=(10, 6))
        for i, label in enumerate(labels):
            data = df[df["label"] == label]["latency_ms"].dropna()
            x = data.sort_values()
            y = pd.Series(1, index=x.index).cumsum() / len(x)
            
            ax.plot(x, y, label=label, color=colors[i % len(colors)], linestyle=line_styles[i % len(line_styles)])
            
        ax.set_title("CDF Overlay of End-to-End Latency")
        ax.set_xlabel("End-to-End Latency (ms)")
        ax.set_ylabel("CDF")
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc="lower right")
        ax.set_ylim((0.0, 1.05))
        fig.tight_layout()
        
        chart_path = os.path.join(output_dir, "cdf_overlay.png")
        fig.savefig(chart_path, dpi=300)
        plt.close(fig)
        logger.info("Wrote combined CDF to %s", chart_path)

