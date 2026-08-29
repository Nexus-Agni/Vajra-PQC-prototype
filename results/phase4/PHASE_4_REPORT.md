# VAJRA-PQC / QS-TIE
# PHASE 4 — GATEWAY A SENDER CONSTRUCTION — FINAL REPORT

## 1. Phase Objective
To implement Gateway A (the sender) against the strictly frozen and previously tested Gateway B. Gateway A safely ingests MISP events via ZeroMQ, extracts them to STIX 2.1, zlib-compresses, signs with ML-DSA-65, evaluates against Outbound PEP logic (TLP marking limits), and securely transmits to Gateway B via PQC hybrid mTLS.

## 2. Scope
Gateway A implementation, local component unit testing, metrics exposition, dead-letter storage, Docker-based end-to-end integration, failure injection, requirements traceability, reproducibility capture, and final evidence gap closure.

## 3. Infrastructure & Environment Distinction (REAL vs MOCK)
As requested, this report explicitly distinguishes between real runtime implementations and mock dependencies used exclusively for testing.

### REAL Infrastructure:
- **Gateway A Implementation:** Fully implemented and executing natively inside the `gateway-a` Docker container using `asyncio`, `pyzmq`, `stix2`, and `prometheus_client`.
- **Gateway B Target:** The actual frozen Phase-3 `gateway-b` container is used as the receiver contract for integration testing.
- **Transport Security:** Actual Python 3.14 + OpenSSL 3.5.7 TLS 1.3 `X25519MLKEM768` hybrid transport is established between Gateway A and Gateway B.
- **Dead-Letter Store:** Real JSONL file appending and bounded memory deque management.

### MOCK Infrastructure:
- **MISP Source:** A mock ZMQ Publisher (`tests/phase4/mock_misp.py`) is used to inject deterministic synthetic events into Gateway A.
- **OpenCTI Sink:** Gateway B is configured to use a synthetic OpenCTI token (`OPENCTI_API_TOKEN=synthetic-token-for-testing`), causing it to bypass physical OpenCTI delivery while still validating all cryptographic and policy boundaries.
- **PKI (Keys/Certs):** Locally generated certificates (`pki/gateway_raw/`, `pki/gateway_nia/`) are used to simulate the actual Certificate Authority.

## 4. Evidence Gap Closure & Issue Resolutions
During the final review, 7 specific issues were addressed:

1. **ISSUE 1 (TLS Negative Tests):** Implemented `TLS timeout` and `wrong server certificate` tests in `test_4_6_to_4_9_transport.py`. All 5 TLS scenarios pass and output to `tls_client_validation.json`.
2. **ISSUE 2 (Dead-Letter maxlen=500):** Explicitly tested the `maxlen=500` boundary by inserting 501 items, verifying oldest item eviction and newest item retention, along with full JSONL append behavior.
3. **ISSUE 3 (Repeated Validation):** Created `repeat_runner.py` which orchestrated 5 independent, clean Docker execution cycles of the Phase-4 validation suite, culminating in `repeated_validation.json`.
4. **ISSUE 4 (Reproducibility):** Reconciled reproducibility metadata by executing `docker inspect` to capture the exact image digests/IDs for both `gateway-a` and `gateway-b`, storing them in `reproducibility.json`.
5. **ISSUE 5 (SECLEVEL=0):** Investigated the usage of `SECLEVEL=0`. Discovered it was a **test-only artifact** inserted for compatibility with mock dummy servers. It is **NOT** required by the actual primary Gateway-A/B runtime. The configuration discrepancy was resolved by stripping `SECLEVEL=0` from the production `PqcTlsClient`, while keeping it explicitly in isolated dummy server tests. The integration suite passes flawlessly with default strong configuration.
6. **ISSUE 6/7/17/18/19 (Real vs Mock / RTM / Phase-3 Regression):** Explicitly distinguished Real/Mock in this section. Expanded the RTM into a comprehensive ~39 row matrix. Executed a full Phase-3 regression suite via `docker compose run --rm --entrypoint python gateway-b tests/phase3/runner.py`, confirming 8/8 Gateway B security tests still pass without regressions.

## 5. Artifact Directory
All evidence is accurately captured in JSON format under `results/phase4/evidence/`:
- `misp_validation.json`
- `stix_validation.json`
- `compression_validation.json`
- `signing_validation.json`
- `policy_validation.json`
- `tls_client_validation.json`
- `wire_protocol_validation.json`
- `ack_nack_validation.json`
- `retry_validation.json`
- `deadletter_validation.json`
- `metrics_validation.json`
- `integration_validation.json`
- `repeated_validation.json`
- `reproducibility.json`

Phase 3 baseline security regression is preserved in `results/phase3/evidence/`.

## 6. Final Decision

```text
PHASE 4 DECISION: GO
```
Gateway A successfully orchestrates the fully signed, policy-enforced, post-quantum protected end-to-end integration path to Gateway B. All test assertions, negative path evaluations, requirements traceability matrices, and evidence generation standards strictly satisfy the research requirements without overclaims.
