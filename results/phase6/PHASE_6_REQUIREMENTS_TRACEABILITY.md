# VAJRA-PQC / QS-TIE - Phase 6 Requirements Traceability Matrix

## Overview
This Traceability Matrix confirms the closure of Phase 6 specifications, tracing the execution of the qualification suite against the live Docker topology.

| Req ID | Requirement Description | Implementation Component | Test Coverage | Evidence Artifact | Status |
|---|---|---|---|---|---|
| 6.1 | Full End-to-End Reliability | `tests/phase6/run_tests.py` | `test_e2e_positive()` | `e2e_positive.jsonl` | PASS |
| 6.1.1 | Process 50+ consecutive events | `gateway_a` pipeline | `test_e2e_positive()` | `e2e_positive.jsonl` | PASS |
| 6.2 | Security Test Matrix | `tests/phase6/run_tests.py` | `test_security_matrix()` | `security_matrix.jsonl` | PASS |
| 6.2.1 | Block Unknown Sender | `tests/phase3/manual_cli.py` | `test_security_matrix()` | `security_matrix.jsonl` | PASS |
| 6.2.2 | Block Invalid/Missing Certs | `tests/phase3/manual_cli.py` | `test_security_matrix()` | `security_matrix.jsonl` | PASS |
| 6.2.3 | Block Invalid Signatures | `tests/phase3/manual_cli.py` | `test_security_matrix()` | `security_matrix.jsonl` | PASS |
| 6.2.4 | Block Malformed STIX | `tests/phase3/manual_cli.py` | `test_security_matrix()` | `security_matrix.jsonl` | PASS |
| 6.2.5 | Enforce Policy Denial | `pep_outbound.py` | `test_security_matrix()` | `security_matrix.jsonl` | PASS |
| 6.3 | Failure Injection | `tests/phase6/run_tests.py` | `test_failure_injection()` | `failure_injection.jsonl` | PASS |
| 6.3.1 | Survive Router Failure | `docker compose stop netem-router` | `test_failure_injection()` | `failure_injection.jsonl` | PASS |
| 6.3.2 | Survive Sink (OpenCTI) Failure | `docker compose stop opencti` | `test_failure_injection()` | `failure_injection.jsonl` | PASS |
| 6.3.3 | Enforce Dead-Lettering on MAX_RETRIES | `gateway_a/pipeline/transmission_worker.py` | `test_failure_injection()` | `failure_injection.jsonl` | PASS |
| 6.4 | Backpressure & Queuing | `tests/phase6/run_tests.py` | `test_backpressure()` | `backpressure.jsonl` | PASS |
| 6.4.1 | Handle 200+ event burst cleanly | `misp_publisher_mock.py` burst | `test_backpressure()` | `backpressure.jsonl` | PASS |
