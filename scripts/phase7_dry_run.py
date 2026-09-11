#!/usr/bin/env python3
import logging
import sys
import os
from benchmark_runner.runner import BenchmarkRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

EVIDENCE_DIR = "/app/results/phase5/evidence"

def main() -> None:
    logger.info("Starting Phase 7 dry run campaign...")
    
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    
    runner = BenchmarkRunner(
        evidence_dir=EVIDENCE_DIR,
        event_count=50,      
        wait_seconds=15,     
        warm_up_discard=10,  
        iterations=1,
    )
    results = runner.run()

    if not results:
        logger.error("No benchmark results produced.")
        sys.exit(1)

    logger.info("Phase 7 dry run complete.")

if __name__ == "__main__":
    main()
