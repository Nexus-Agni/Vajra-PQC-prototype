#!/usr/bin/env python3
"""Benchmark campaign CLI entrypoint.

Thin wrapper that instantiates BenchmarkRunner with production defaults
and executes the full campaign.  All logic lives in the benchmark_runner
package modules; this file is only the Docker CMD target.
"""
import logging
import sys

from benchmark_runner.runner import BenchmarkRunner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


EVIDENCE_DIR = "/app/results/phase5/evidence"

def main() -> None:
    logger.info("Starting benchmark campaign...")
    runner = BenchmarkRunner(
        evidence_dir=EVIDENCE_DIR,
    )
    results = runner.run()

    if not results:
        logger.error("No benchmark results produced — check gateway logs.")
        sys.exit(1)

    logger.info(
        "Benchmark complete: %d configurations tested. "
        "Reports saved to %s/",
        len(results),
        EVIDENCE_DIR,
    )


if __name__ == "__main__":
    main()
