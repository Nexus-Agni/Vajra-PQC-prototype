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

    def compute(self, df: pd.DataFrame, warm_up_discard: int = 100) -> Optional[Dict[str, Any]]:
        """Calculate mean, percentile, and breakdown latencies.

        Args:
            df: Merged DataFrame with columns tx_id, t_received,
                t_extracted, t_signed, t_acked, retry_count,
                t_received_b, t_verified_b, t_ingested_b.
            warm_up_discard: Number of initial events to discard to prevent cold-start anomalies.

        Returns:
            A dict with academic-grade statistical metrics.
            Returns None if the DataFrame has insufficient data after discard.
        """
        if df.empty or len(df) <= warm_up_discard:
            return None

        # Discard warmup events
        df = df.iloc[warm_up_discard:].copy()

        # Derived latency columns (ns → ms)
        total = (df["t_ingested_b"] - df["t_received"]) / self.NS_TO_MS
        
        n = len(total)
        mean_latency = float(total.mean())
        std_dev = float(total.std()) if n > 1 else 0.0
        
        import math
        margin_of_error = 1.96 * (std_dev / math.sqrt(n)) if n > 0 else 0.0

        return {
            "median_latency_ms": float(total.median()),
            "mean_latency_ms": mean_latency,
            "std_dev_ms": std_dev,
            "ci_95_lower": mean_latency - margin_of_error,
            "ci_95_upper": mean_latency + margin_of_error,
            "p95_latency_ms": float(total.quantile(0.95)),
            "p99_latency_ms": float(total.quantile(0.99)),
            "p999_latency_ms": float(total.quantile(0.999)),
            "mean_retries": float(df["retry_count"].mean()),
            "count": n,
        }
