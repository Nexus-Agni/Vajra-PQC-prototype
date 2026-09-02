"""Telemetry ingestion: parse gateway JSONL files and merge by transaction ID."""
from __future__ import annotations

import json
import logging
import os
from typing import List, Dict, Any

import pandas as pd

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """Ingest and merge telemetry JSONL from Gateway A and Gateway B.

    Each gateway writes newline-delimited JSON to its own file.  This
    collector parses both, filters for successfully ACKed transactions,
    flattens the nested ``telemetry`` dict into columns, and merges the
    two sides on ``transaction_id`` so that downstream metrics can
    correlate sender and receiver timestamps.
    """

    def __init__(
        self,
        telemetry_a_path: str = "results/phase5/evidence/telemetry_a.jsonl",
        telemetry_b_path: str = "results/phase5/evidence/telemetry_b.jsonl",
    ) -> None:
        self._path_a = telemetry_a_path
        self._path_b = telemetry_b_path

    # ── public API ──────────────────────────────────────────────────

    def collect(self) -> pd.DataFrame:
        """Parse both JSONL files, merge on transaction_id.

        Returns a DataFrame with columns:
            tx_id, t_received, t_extracted, t_signed, t_acked, retry_count,
            t_received_b, t_verified_b, t_ingested_b

        Only transactions that are ACKED in *both* gateways are included.
        Returns an empty DataFrame if either file is missing or has no
        usable records.
        """
        a_events = self._parse_jsonl(self._path_a)
        b_events = self._parse_jsonl(self._path_b)

        a_acked = [
            e for e in a_events
            if e.get("state", "").upper() == "ACKED"
        ]
        b_acked = [
            e for e in b_events
            if e.get("state", "").upper() == "ACKED"
        ]

        if not a_acked or not b_acked:
            return pd.DataFrame()

        df_a = pd.DataFrame([
            {"tx_id": e["transaction_id"], **e["telemetry"]}
            for e in a_acked
        ])
        df_b = pd.DataFrame([
            {"tx_id": e["transaction_id"], **e["telemetry"]}
            for e in b_acked
        ])

        return pd.merge(df_a, df_b, on="tx_id")

    # ── internals ───────────────────────────────────────────────────

    @staticmethod
    def _parse_jsonl(path: str) -> List[Dict[str, Any]]:
        """Parse a JSONL file, skipping malformed lines."""
        if not os.path.exists(path):
            logger.warning("Telemetry file not found: %s", path)
            return []

        events: List[Dict[str, Any]] = []
        with open(path, "r") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(
                        "Skipping malformed JSON at %s:%d", path, line_no
                    )
        return events
