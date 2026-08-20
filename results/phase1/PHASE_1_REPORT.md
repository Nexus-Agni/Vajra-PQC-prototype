# PHASE 1 — SHARED CONTRACT VALIDATION REPORT

## 1. Phase Objective

The objective of Phase 1 was to build the common language between Gateway A and Gateway B before either gateway exists. This includes establishing one authoritative protocol contract that both future gateways will consume, encompassing the shared transaction model, enums, error models, fingerprint utilities, protocol definitions, protobuf serialization, and frame encoding/decoding.

## 2. Repository Baseline

- **Starting Commit**: Initial setup/baseline.
- **Branch**: main
- **Repository State**: Clean, prior to Phase 1 additions containing only the Phase 0 PID document.

## 3. Implementation Summary

- `qstie.proto`: Authoritative protobuf schema for `TransactionEnvelope`
- `qstie_common.models.TransactionEnvelope`: Application-level transaction model
- `qstie_common.enums.protocol_enums`: Message types, TLP markings, NACK reasons, and Transaction States
- `qstie_common.errors.protocol_errors`: Shared error hierarchy including frame and envelope errors
- `qstie_common.fingerprints.utils`: Shared fingerprint calculation utility (SHA-256)
- `qstie_common.protocol.frame_codec`: Stream-safe application frame encoder/decoder enforcing maximum frame size
- `test_vectors`: Golden vectors and size evidence generation

## 4. Files Added/Modified

**Added**:
- `proto/qstie.proto`
- `packages/qstie-common/pyproject.toml`
- `packages/qstie-common/README.md`
- `packages/qstie-common/qstie_common/__init__.py`
- `packages/qstie-common/qstie_common/enums/protocol_enums.py`
- `packages/qstie-common/qstie_common/enums/__init__.py`
- `packages/qstie-common/qstie_common/errors/protocol_errors.py`
- `packages/qstie-common/qstie_common/errors/__init__.py`
- `packages/qstie-common/qstie_common/fingerprints/utils.py`
- `packages/qstie-common/qstie_common/fingerprints/__init__.py`
- `packages/qstie-common/qstie_common/protocol/frame_codec.py`
- `packages/qstie-common/qstie_common/protocol/__init__.py`
- `packages/qstie-common/qstie_common/protocol/qstie_pb2.py` (Generated)
- `packages/qstie-common/qstie_common/models/envelope.py`
- `packages/qstie-common/qstie_common/models/__init__.py`
- `tests/unit/test_envelope.py`
- `tests/protocol/test_frame_codec.py`
- `tests/protocol/test_stream_fragmentation.py`
- `tests/protocol/test_wire_inspection.py`
- `tests/security/test_security.py`
- `tests/interoperability/test_interoperability.py`
- `tests/regression/test_golden_vectors.py`
- `run_repeated_tests.py`

## 5. Automated Tests

Total tests: 40
Passed: 40
Failed: 0
Skipped: 0

## 6. Security Tests

Total security tests: 15
Passed: 15
Failed: 0

## 7. Interoperability

- Gateway A encoder → Gateway B decoder: PASS
- Gateway B encoder → Gateway A decoder: PASS

## 8. Golden Vectors

- `normal` vector: Validated and stored.
- `unicode` vector: Validated and stored.
Status: PASS

## 9. Stream/Fragmentation Testing

- Partial header: Correctly handled.
- Partial payload: Correctly handled.
- Multiple frames: Successively decoded.
- Arbitrary fragmentation: Reconstructed and decoded successfully in `test_random_fragmentation`.
- Repeated randomized tests: Included in 50-run campaign.

## 10. Maximum Frame Size

- **Configured value**: 10 MB (10,485,760 bytes)
- **Rationale**: Provides an upper bound on payload size large enough for highly compressed threat intelligence bundles without allowing unbounded memory allocation on the Gateway processing layer.
- **Test results**: Exceeding the maximum payload size (either actual or declared in header) raises `OversizedFrameError`.
- **Rejection behavior**: Immediate rejection without allocating payload buffer.

## 11. Serialized Size Evidence

| Scenario | Protobuf Payload Size (bytes) | Complete Frame Size (bytes) |
|---|---|---|
| empty | 11 | 16 |
| normal | 73 | 78 |
| unicode | 58 | 63 |
| binary_signature | 2045 | 2050 |
| large_payload | 1000045 | 1000050 |

## 12. Fingerprint Semantics

- **Input Bytes**: Raw, explicit binary bytes (`bytes` in Python).
- **Algorithm**: SHA-256 (`hashlib.sha256()`).
- **Output Representation**: Canonical lowercase hex string.
- **Test Vector Verification**: Tested in `test_fingerprint_preservation` where binary data correctly maps to its canonical hex string and survives serialization/deserialization identically.

## 13. Environment

- **Python Version**: 3.14.6 (Validated in containerized Linux environment as per PID baseline)
- **OS**: Linux (python:3.14.6-slim Docker container)
- **Protobuf**: 7.35.1
- **Pytest**: 9.1.1
- **Git branch**: main

## 14. Important Observations

- The `>BI` format header adds precisely 5 bytes of overhead per message.
- Stream frame decoder properly buffers incomplete segments avoiding memory leaks or data truncation, enabling reliable network transport integration for asyncio code in later phases.
- Valid protobuf encoded bytes will deterministically map correctly to and from models, preserving complex unicode entities and raw binary structures seamlessly. 

## 15. Thesis-Relevant Findings

- **Wire Overhead**: The application framing overhead is negligible (5 bytes per message), keeping bandwidth usage directly proportional to the STIX content size and ML-DSA-65 signatures.
- **Binary Signature Handling**: Binary signatures fit securely in protobuf's `bytes` field without base64 inflation or encoding corruption.
- **Protocol Robustness**: Mitigates oversized-length-driven memory exhaustion during frame parsing by rejecting oversized declared lengths before payload allocation.
- **Interoperability Properties**: Separating the contract definition and exposing strict binary encode/decode operations cleanly insulates the application logic. Both simulated Gateway edges (shared Gateway-A/Gateway-B protocol interoperability validation, not full integration) safely read identically mapped payloads.

## 16. Known Issues

None

## 17. Blockers

NONE

## 18. Evidence Location

- Source schemas and models: `proto/` and `packages/qstie-common/`
- Test cases: `tests/`
- Golden Vectors Evidence: `results/phase1/evidence/golden_vectors.json`
- Size Evidence: `results/phase1/evidence/size_evidence.json`
- Test execution log: `results/phase1/logs/repeated_validation.log`
- This Report: `results/phase1/PHASE_1_REPORT.md`

## 19. Final Gate Decision

GO
