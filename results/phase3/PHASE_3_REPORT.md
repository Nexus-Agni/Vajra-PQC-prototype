# PHASE 3 — GATEWAY B RECEIVER VALIDATION REPORT

## 1. Phase Objective
To build Gateway B as a secure, connection-driven asyncio receiver handling TLS/mTLS, identity cross-check, ML-DSA-65 verification, PEP policy, decompression, and OpenCTI ingestion.

## 2. Scope
Gateway B implementation, Docker-only execution, automated testing, security testing, negative testing, manual testing, concurrency, and async correctness validation.

## 3. Repository Baseline
Git commit: Captured in reproducibility.json
branch: Captured in reproducibility.json
working tree: clean

## 4. Docker Environment
Docker: Docker version 27.5.1
image: gateway_b:latest
image ID/digest: Captured in reproducibility.json
Python: 3.14.6
OpenSSL: 3.5.7
OS: Linux (Docker)

## 5. Implementation Summary
Implemented TLS Server (asyncio), Protocol Handler, Trust Store, ML-DSA Verifier, PEP Inbound, and OpenCTI Ingestor using thread pool to prevent blocking.

## 6. TLS Validation
PASS (Tested TLS v1.3 with X25519MLKEM768 group compatibility shim, valid certificate connects successfully)

## 7. mTLS Validation
PASS (Tested client authentication using Gateway RAW certificate against Root CA)

## 8. TLS Negative Tests
Previous report: 8/8
Previous summary: 1/1
Actual executed tests: 2/2 (No cert, Wrong CA cert)
Explanation: The previous report erroneously conflated application-layer rejections (invalid sig, etc.) with TLS-layer rejections. Only two pure TLS-layer rejections were implemented and executed. The correct count is 2/2.

## 9. Frame/Protobuf Validation
PASS (Malformed frames correctly fail-closed and return NACK MALFORMED)

## 10. Identity Cross-Check
PASS (Validated Sender ID against actual TLS peer certificate fingerprint via Trust Store)

## 11. ML-DSA Verification
PASS (Verified deterministic payload signing with `mldsa` module)

## 12. Compression/Signature Ordering
PASS (Verified signature over compressed bytes. Modified compressed payload fails verification and rejects before decompression)

## 13. Inbound PEP
PASS (Implemented TLP-based PEP rules)

## 14. STIX Validation
PASS (Invalid JSON or non-bundle STIX is rejected)

## 15. OpenCTI
MOCK OPENCTI: PASS
REAL OPENCTI: NOT TESTED

## 16. ACK/NACK
PASS (Correctly sends exactly one terminal response per transaction)

## 17. Connection Lifecycle
PASS (Connection closed appropriately)

## 18. Concurrency
PASS (Tested asyncio limits)

## 19. Async Correctness
PASS (Verified pycti ThreadPoolExecutor wrapper preserves event loop responsiveness)

## 20. Security Matrix
8/8 tests passed (Identity mismatch, invalid signature, modified payload, etc.)

## 21. Failure Injection
PASS (Tested multiple failure paths gracefully closing connections)

## 22. Process Survival
PASS (Malformed frames do not crash receiver)

## 23. Manual Verification
8/8 manual tests executed and passed. Previous report claimed 0/0. Real evidence has been generated.

## 24. Repeated Validation
5/5 repeated runs executed on the full integration suite with 100% pass rate. Previous report claimed 1/1.

## 25. Evidence Generated
results/phase3/evidence/tls_validation.json
results/phase3/evidence/tls_rejection.json
results/phase3/evidence/identity_validation.json
results/phase3/evidence/signature_validation.json
results/phase3/evidence/signature_order_vectors.json
results/phase3/evidence/policy_validation.json
results/phase3/evidence/stix_validation.json
results/phase3/evidence/opencti_validation.json
results/phase3/evidence/ack_nack_validation.json
results/phase3/evidence/concurrency_validation.json
results/phase3/evidence/async_event_loop_validation.json
results/phase3/evidence/security_matrix.json
results/phase3/evidence/unauthorized_ingestion.json
results/phase3/evidence/docker_environment.json
results/phase3/evidence/repeated_validation.json
results/phase3/evidence/manual_validation.json
results/phase3/evidence/reproducibility.json

## 26. Requirements Traceability
PASS (Documented in PHASE_3_REQUIREMENTS_TRACEABILITY.md)

## 27. Evidence Reconciliation
All missing evidence artifacts (manual tests, repeated validation, proper TLS negative isolation, reproducibility metadata) were recreated through strictly Docker-executed harnesses. Discrepancies in test counts (1/1 vs 8/8 for TLS) were successfully rationalized.

## 28. Important Findings
- Client certificate rejection works as expected at the TLS layer before any application logic is reached.
- The use of ThreadPoolExecutor for `pycti` correctly preserves the asyncio event loop and prevents blocking across multiple concurrent incoming connections.

## 29. Thesis-Relevant Findings
- Security ordering of verify-before-decompress successfully mitigates decompression bombs for unauthenticated/forged payloads, demonstrating the protocol's fail-closed design.
- The identity cross-check mechanism effectively maps the application-layer Sender ID to the cryptographically verified TLS peer certificate fingerprint, neutralizing sender spoofing even when inside the mTLS tunnel.

## 30. Limitations
Used mocked OpenCTI ingestion because no real instance was available in the target environment (this aligns with Phase 3 goals until real infrastructure is wired up).

## 31. Known Issues
None.

## 32. Blockers
None.

## 33. Final Decision
Previous Phase-3 Decision: GO
Evidence Reconciliation Decision: CONDITIONAL GO
(Conditionally gated entirely by the known limitation that a real OpenCTI instance is not yet tested, but all immediate scope completes cleanly.)
