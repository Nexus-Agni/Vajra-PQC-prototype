#!/usr/bin/env python3
"""Full Phase 7 benchmark execution: 5 iterations × 4 configurations.

Gateways write telemetry to results/phase5/evidence/telemetry_{a,b}.jsonl
(hardcoded in gateway_a/b/observability/telemetry_logger.py).
Reports and charts are written to stat-data/phase7/.
"""
import logging
import subprocess
import sys
import os
from benchmark_runner.runner import BenchmarkRunner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Gateways write telemetry here (hardcoded in their telemetry_logger.py)
TELEMETRY_A = "/app/results/phase5/evidence/telemetry_a.jsonl"
TELEMETRY_B = "/app/results/phase5/evidence/telemetry_b.jsonl"

# Reports and charts go here
OUTPUT_DIR = "/app/stat-data/phase7"

# Mock publisher script (in repo) and its target path inside the MISP container
MOCK_PUBLISHER_SRC = "/app/tests/phase6/misp_publisher_mock.py"
MOCK_PUBLISHER_DST = "/tmp/misp_publisher_mock.py"


def _resolve_misp_container() -> str:
    """Resolve the MISP container name via Compose labels."""
    result = subprocess.run(
        "docker ps "
        "--filter label=com.docker.compose.project=prototype-implementation-main "
        "--filter label=com.docker.compose.service=misp "
        "--format '{{.Names}}'",
        shell=True, capture_output=True, text=True,
    )
    name = result.stdout.strip().strip("'").split("\n")[0]
    return name or "misp"


def _setup_misp_mock() -> None:
    """Copy the ZMQ publisher mock into the MISP container.

    The benchmark runner's _inject_events() runs
      docker exec <misp> python3 /tmp/misp_publisher_mock.py <N> green
    so the script must exist inside the container before the campaign starts.
    """
    misp = _resolve_misp_container()
    logger.info("Copying publisher mock into %s:%s", misp, MOCK_PUBLISHER_DST)

    result = subprocess.run(
        f"docker cp {MOCK_PUBLISHER_SRC} {misp}:{MOCK_PUBLISHER_DST}",
        shell=True, capture_output=True, text=True,
    )
    if result.returncode != 0:
        logger.error("docker cp failed: %s", result.stderr)
        sys.exit(1)

    # Verify the file landed
    verify = subprocess.run(
        f"docker exec {misp} python3 -c \"import os; assert os.path.exists('{MOCK_PUBLISHER_DST}')\"",
        shell=True, capture_output=True, text=True,
    )
    if verify.returncode != 0:
        logger.error("Publisher mock not found inside %s after copy", misp)
        sys.exit(1)

    logger.info("Publisher mock verified inside %s", misp)


def main() -> None:
    logger.info("Starting Phase 7 Full Benchmark execution (5 iterations)...")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(TELEMETRY_A), exist_ok=True)

    _setup_misp_mock()

    runner = BenchmarkRunner(
        evidence_dir=OUTPUT_DIR,
        telemetry_a_path=TELEMETRY_A,
        telemetry_b_path=TELEMETRY_B,
        event_count=5000,
        wait_seconds=900,
        warm_up_discard=1000,
        iterations=5,
    )

    results = runner.run()

    if not results:
        logger.error("No benchmark results produced.")
        sys.exit(1)

    # Check if there are any missing iterations or missing configurations
    expected_count = 5 * 2 * 2  # 5 iterations, 2 crypto, 2 profiles
    if len(results) != expected_count:
        logger.error(
            "Missing data! Expected %d results, but got %d",
            expected_count,
            len(results),
        )
        sys.exit(1)

    logger.info(
        "Phase 7 benchmark complete. %d/%d results saved to %s",
        len(results),
        expected_count,
        OUTPUT_DIR,
    )


if __name__ == "__main__":
    main()
