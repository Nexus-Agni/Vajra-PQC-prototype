# 09: Phase 7 Traceability Report

**What to build:** A formal `PHASE_7_REPORT.md` document in `results/phase5/` that serves as the reproducibility package for the thesis. This is the document a reviewer, thesis examiner, or Artifact Evaluation Committee member reads to verify that the benchmark methodology is sound, the results are reproducible, and the claims are defensible.

This is NOT a code change — it is a documentation deliverable that synthesizes the finalized benchmark data, the generated graphs, and the research findings from `.scratch/research/BENCHMARKING_METHODOLOGY_STANDARDS.md` into a single, self-contained report.

After this ticket, the report is ready to be cited directly in the thesis evaluation chapter. A reviewer can read it and understand exactly what was measured, how, on what hardware, under what network conditions, with what statistical methodology, and what the results show.

**Blocked by:** 08: Execute Full Academic Benchmark Campaign

**Status:** resolved

- [x] Create `results/phase7/PHASE_7_REPORT.md` with the following sections:

### Section 1: Environment
- [x] Document the exact hardware: Intel Core i5-10300H @ 2.50 GHz (4C/8T, Comet Lake), 16 GB RAM, NVIDIA GTX 1650, Windows 64-bit.
- [x] Document software versions: Docker version, Docker Compose version, OpenSSL version (from within the gateway containers), Python version, OS kernel version.
- [x] Document the Docker resource pinning applied to gateway containers (CPU/memory limits).

### Section 2: Methodology
- [x] Document the exact netem parameters for each network profile: stable (no constraints) and adverse (delay 50ms ± 10ms jitter, 3% packet loss, 5 Mbit bandwidth cap).
- [x] Document the event injection methodology: 1,000 STIX 2.1 events per configuration per iteration, 5 independent iterations, first 100 events discarded as warm-up.
- [x] Document the cryptographic suites under test: Classical baseline (TLS 1.3 X25519 key exchange + ECDSA P-256 transport cert + ECDSA P-256 payload signing) vs. Hybrid PQC (TLS 1.3 X25519MLKEM768 key exchange + ML-DSA-65 transport cert + ML-DSA-65 payload signing).
- [x] Document the telemetry collection points: Gateway A timestamps (t_received, t_extracted, t_signed, t_acked) and Gateway B timestamps (t_verified_b, t_ingested_b).

### Section 3: Statistical Methodology
- [x] State which percentiles are reported (P50, P95, P99, P99.9) and why median is preferred over mean.
- [x] State the confidence interval methodology (95% CI = mean ± 1.96 × σ/√n).
- [x] State the warm-up exclusion policy and justify it (cache priming, branch predictor training).

### Section 4: Results
- [x] Include the full results table from `benchmark_report.csv` formatted as a markdown table.
- [x] Embed the box-and-whisker comparison plot with an academic caption explaining what it shows.
- [x] Embed the CDF overlay plot with an academic caption.
- [x] Embed per-configuration CDF plots if they add value.

### Section 5: Analysis and Conclusion
- [x] Summarize the overhead delta between classical and hybrid PQC suites under both network profiles.
- [x] Discuss tail latency behaviour (P99/P99.9) under adverse conditions.
- [x] Note any surprising findings or anomalies.

### Section 6: Raw Data References
- [x] Link to `results/phase5/evidence/benchmark_report.csv`.
- [x] Link to `results/phase5/evidence/telemetry_a.jsonl` and `telemetry_b.jsonl`.
- [x] Link to all generated PNG graph files.

## Answer

Resolved. Generated results/phase7/PHASE_7_REPORT.md
