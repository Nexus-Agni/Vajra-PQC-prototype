"""Metrics calculation: compute latency statistics from merged telemetry."""
from __future__ import annotations

from typing import Dict, Any, Optional

import pandas as pd


class MetricsCalculator:
    """Compute benchmark metrics from a merged telemetry DataFrame.

    Expects the DataFrame produced by ``TelemetryCollector.collect()``,
    with nanosecond timestamps from Gateway A and Gateway B.
    """

    NS_TO_MS = 1e6  # nanoseconds → milliseconds divisor

    def compute(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Calculate mean, percentile, and breakdown latencies.

        Args:
            df: Merged DataFrame with columns tx_id, t_received,
                t_extracted, t_signed, t_acked, retry_count,
                t_received_b, t_verified_b, t_ingested_b.

        Returns:
            A dict with:
              - mean_latency_ms, p95_latency_ms, p99_latency_ms
              - mean_retries, count
              - mean_extraction_ms, mean_signing_ms, mean_network_verify_ms
            Returns None if the DataFrame is empty.
        """
        if df.empty:
            return None

        # Derived latency columns (ns → ms)
        total = (df["t_ingested_b"] - df["t_received"]) / self.NS_TO_MS
        extraction = (df["t_extracted"] - df["t_received"]) / self.NS_TO_MS
        signing = (df["t_signed"] - df["t_extracted"]) / self.NS_TO_MS
        network_verify = (df["t_verified_b"] - df["t_signed"]) / self.NS_TO_MS

        return {
            "mean_latency_ms": float(total.mean()),
            "p95_latency_ms": float(total.quantile(0.95)),
            "p99_latency_ms": float(total.quantile(0.99)),
            "mean_retries": float(df["retry_count"].mean()),
            "count": len(df),
            "mean_extraction_ms": float(extraction.mean()),
            "mean_signing_ms": float(signing.mean()),
            "mean_network_verify_ms": float(network_verify.mean()),
        }
