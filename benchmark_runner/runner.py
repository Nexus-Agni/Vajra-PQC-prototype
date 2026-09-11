"""Benchmark runner: orchestrate benchmark campaigns across crypto and network profiles."""
from __future__ import annotations

import logging
import os
import time
from typing import Callable, Dict, Any, List, Optional

import pandas as pd

from benchmark_runner.config import (
    BenchmarkConfig,
    CryptoConfig,
    CLASSICAL,
    HYBRID_PQC,
)
from benchmark_runner.metrics import MetricsCalculator
from benchmark_runner.network import NetworkController, _default_exec, ExecFn
from benchmark_runner.report import ReportGenerator
from benchmark_runner.telemetry import TelemetryCollector

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Orchestrate benchmark test campaigns.

    For each crypto mode × network profile combination:
    1. Toggle the netem-router to the desired profile.
    2. Probe actual RTT via ping.
    3. Inject events through the MISP publisher mock.
    4. Wait for events to propagate.
    5. Collect telemetry from both gateways.
    6. Compute metrics.
    7. Generate CDF chart.

    After all combinations, generate the final CSV report and summary chart.

    In production, the runner controls Docker containers via ``exec_fn``.
    In tests, ``exec_fn`` is replaced with a mock at the system boundary.
    """

    def __init__(
        self,
        evidence_dir: str = "/app/results/phase5/evidence",
        telemetry_a_path: Optional[str] = None,
        telemetry_b_path: Optional[str] = None,
        exec_fn: ExecFn = _default_exec,
        event_count: int = 5000,
        wait_seconds: int = 900,
        warm_up_discard: int = 1000,
        compose_file: str = "/app/compose.yaml",
        iterations: int = 5,
    ) -> None:
        self._evidence_dir = evidence_dir
        self._telemetry_a = telemetry_a_path or os.path.join(
            evidence_dir, "telemetry_a.jsonl"
        )
        self._telemetry_b = telemetry_b_path or os.path.join(
            evidence_dir, "telemetry_b.jsonl"
        )
        self._exec = exec_fn
        self._event_count = event_count
        self._warm_up_discard = warm_up_discard
        self._wait_seconds = wait_seconds
        self._compose_file = compose_file
        self._iterations = iterations

        self._network = NetworkController(exec_fn=exec_fn)
        self._calc = MetricsCalculator()
        self._reporter = ReportGenerator()

    # ── public API ──────────────────────────────────────────────────

    def run(self) -> List[Dict[str, Any]]:
        """Execute the full benchmark campaign.

        Returns the list of per-combination result dicts.
        """
        logger.info("Starting benchmark campaign")
        os.makedirs(self._evidence_dir, exist_ok=True)

        results: List[Dict[str, Any]] = []
        
        # We collect all raw latency series for combined plotting
        raw_latencies = []

        for iteration in range(1, self._iterations + 1):
            logger.info("Starting iteration %d/%d", iteration, self._iterations)
            for crypto_cfg in [CLASSICAL, HYBRID_PQC]:
                logger.info("Switching to crypto mode: %s", crypto_cfg.group)
                self._set_crypto_env(crypto_cfg)
                self._restart_gateways()
                time.sleep(min(self._wait_seconds, 10))
    
                for profile in ["stable", "adverse"]:
                    logger.info(
                        "Running profile '%s' for crypto '%s' (Iteration %d)",
                        profile,
                        crypto_cfg.group,
                        iteration
                    )
                    self._network.toggle_profile(profile)
                    time.sleep(min(self._wait_seconds, 2))
    
                    avg_rtt = self._network.probe_rtt()
                    logger.info("Measured RTT: %.3f ms", avg_rtt)
    
                    self._clear_telemetry()
                    self._inject_events(self._event_count)
                    time.sleep(self._wait_seconds)
    
                    result = self._collect_and_compute(
                        crypto_cfg.group, profile, avg_rtt
                    )
                    if result:
                        result["iteration"] = iteration
                        results.append(result)
    
                        # Generate per-configuration CDF (we might overwrite this with combined data, but keeping per-iteration structure for now)
                        # To correctly match the prompt, CDF and box plots will be generated using all data in report.py
                        # We save raw latency series for the reporter to use
                        series = self._get_latency_series()
                        if series is not None:
                            raw_latencies.append({
                                "crypto": crypto_cfg.group,
                                "profile": profile,
                                "iteration": iteration,
                                "latency": series
                            })

        # Final report
        self._reporter.generate(results, raw_latencies, self._evidence_dir)
        logger.info(
            "Benchmark complete. Reports saved to %s", self._evidence_dir
        )
        return results

    # ── internals ───────────────────────────────────────────────────

    def _set_crypto_env(self, cfg: CryptoConfig) -> None:
        """Set environment variables for the crypto mode."""
        os.environ["HYBRID_GROUP"] = cfg.group
        os.environ["A_CERT_PATH"] = cfg.a_cert_path
        os.environ["A_KEY_PATH"] = cfg.a_key_path
        os.environ["A_PAYLOAD_KEY_PATH"] = cfg.a_payload_key_path
        os.environ["A_CA_TRUST_PATH"] = cfg.a_ca_trust_path
        os.environ["B_CERT_PATH"] = cfg.b_cert_path
        os.environ["B_KEY_PATH"] = cfg.b_key_path
        os.environ["B_CA_TRUST_PATH"] = cfg.b_ca_trust_path
        os.environ["TRUST_STORE_PATH"] = cfg.trust_store_path

    def _restart_gateways(self) -> None:
        """Restart gateway containers to pick up new crypto env."""
        self._exec(
            f"docker compose -f {self._compose_file} up -d gateway-a gateway-b"
        )

    def _clear_telemetry(self) -> None:
        """Remove telemetry files to start fresh for each combination."""
        for path in (self._telemetry_a, self._telemetry_b):
            if os.path.exists(path):
                os.remove(path)

    def _inject_events(self, count: int) -> None:
        """Trigger MISP event injection via the publisher mock.

        Resolves the actual MISP container name via Compose labels,
        then ``docker exec``s into it to run the publisher script.
        """
        misp = self._resolve_container("misp")
        self._exec(
            f"docker exec {misp} python3 /tmp/misp_publisher_mock.py {count} green"
        )

    def _resolve_container(self, service: str) -> str:
        """Resolve a Compose service name to its running container name."""
        from benchmark_runner.network import COMPOSE_PROJECT
        cmd = (
            f"docker ps "
            f"--filter label=com.docker.compose.project={COMPOSE_PROJECT} "
            f"--filter label=com.docker.compose.service={service} "
            f"--format '{{{{.Names}}}}'"
        )
        result = self._exec(cmd).strip().strip("'").split("\n")[0]
        if not result:
            logger.warning(
                "Could not resolve container for '%s', using service name",
                service,
            )
            return service
        return result

    def _collect_and_compute(
        self, crypto: str, profile: str, avg_rtt: float
    ) -> Optional[Dict[str, Any]]:
        """Collect telemetry and compute metrics for one combination."""
        collector = TelemetryCollector(self._telemetry_a, self._telemetry_b)
        df = collector.collect()

        if df.empty:
            logger.warning(
                "No completed transactions for %s/%s", crypto, profile
            )
            return None

        metrics = self._calc.compute(df, warm_up_discard=self._warm_up_discard)
        if metrics is None:
            return None

        metrics["crypto"] = crypto
        metrics["profile"] = profile
        metrics["avg_rtt_ms"] = avg_rtt
        return metrics

    def _get_latency_series(self, warm_up_discard: Optional[int] = None) -> Optional[pd.Series]:
        """Get the raw latency series for the current combination."""
        collector = TelemetryCollector(self._telemetry_a, self._telemetry_b)
        df = collector.collect()
        discard = warm_up_discard if warm_up_discard is not None else self._warm_up_discard
        if df.empty or len(df) <= discard:
            return None
        
        df = df.iloc[discard:].copy()
        return (df["t_ingested_b"] - df["t_received"]) / 1e6
