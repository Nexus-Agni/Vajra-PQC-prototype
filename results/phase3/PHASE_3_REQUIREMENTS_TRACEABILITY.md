# PHASE 3 REQUIREMENTS TRACEABILITY

| Requirement | Implementation file | Test file | Test name | Expected result | Actual result | Evidence artifact | Status |
|---|---|---|---|---|---|---|---|
| TLS server | `gateway_b/transport/tls_server.py` | `tests/phase3/runner.py` | `tls_no_cert` | Reject | Reject | `security_matrix.json` | PASS |
| TLS 1.3 | `gateway_b/transport/tls_server.py` | `tests/phase3/runner.py` | `happy_path` | Success | Success | `security_matrix.json` | PASS |
| mTLS | `gateway_b/transport/tls_server.py` | `tests/phase3/runner.py` | `happy_path` | Success | Success | `security_matrix.json` | PASS |
| client certificate requirement | `gateway_b/transport/tls_server.py` | `tests/phase3/runner.py` | `tls_no_cert` | Reject | Reject | `security_matrix.json` | PASS |
| trusted CA | `gateway_b/transport/tls_server.py` | `tests/phase3/runner.py` | `happy_path` | Success | Success | `security_matrix.json` | PASS |
| hybrid group | `gateway_b/transport/tls_server.py` | `tests/phase3/runner.py` | `happy_path` | Success | Success | `security_matrix.json` | PASS |
| frame decoding | `gateway_b/transport/protocol.py` | `tests/phase3/runner.py` | `happy_path` | Success | Success | `security_matrix.json` | PASS |
| protobuf decoding | `gateway_b/transport/protocol.py` | `tests/phase3/runner.py` | `happy_path` | Success | Success | `security_matrix.json` | PASS |
| identity cross-check | `gateway_b/transport/protocol.py` | `tests/phase3/runner.py` | `identity_mismatch` | NACK IDENTITY_MISMATCH | NACK IDENTITY_MISMATCH | `security_matrix.json` | PASS |
| signature verification | `gateway_b/crypto/verifier.py` | `tests/phase3/runner.py` | `invalid_sig` | NACK SIG_INVALID | NACK SIG_INVALID | `security_matrix.json` | PASS |
| compressed-byte signature ordering | `gateway_b/crypto/verifier.py` | `tests/phase3/runner.py` | `modified_compressed` | NACK SIG_INVALID | NACK SIG_INVALID | `security_matrix.json` | PASS |
| inbound PEP | `gateway_b/policy/pep_inbound.py` | `tests/phase3/runner.py` | `policy_denied` | NACK POLICY_DENIED | NACK POLICY_DENIED | `security_matrix.json` | PASS |
| policy denial | `gateway_b/policy/pep_inbound.py` | `tests/phase3/runner.py` | `policy_denied` | NACK POLICY_DENIED | NACK POLICY_DENIED | `security_matrix.json` | PASS |
| decompression | `gateway_b/transport/protocol.py` | `tests/phase3/runner.py` | `happy_path` | Success | Success | `security_matrix.json` | PASS |
| STIX validation | `gateway_b/transport/protocol.py` | `tests/phase3/runner.py` | `malformed_stix` | NACK MALFORMED | NACK MALFORMED | `security_matrix.json` | PASS |
| OpenCTI executor | `gateway_b/ingestion/stix_ingestor.py` | `tests/phase3/runner.py` | `happy_path` | Success | Success | `security_matrix.json` | PASS |
| OpenCTI success | `gateway_b/ingestion/stix_ingestor.py` | `tests/phase3/runner.py` | `happy_path` | Success | Success | `security_matrix.json` | PASS |
| OpenCTI failure | `gateway_b/ingestion/stix_ingestor.py` | `tests/phase3/runner.py` | `opencti_reject` | NACK INGEST_FAILED | NACK INGEST_FAILED | `security_matrix.json` | PASS |
| ACK | `gateway_b/transport/protocol.py` | `tests/phase3/runner.py` | `happy_path` | ACK | ACK | `security_matrix.json` | PASS |
| NACK | `gateway_b/transport/protocol.py` | `tests/phase3/runner.py` | `invalid_sig` | NACK | NACK | `security_matrix.json` | PASS |
| connection close | `gateway_b/transport/protocol.py` | `tests/phase3/runner.py` | `happy_path` | Connection Close | Connection Close | `security_matrix.json` | PASS |
| concurrency | `gateway_b/transport/tls_server.py` | `tests/phase3/runner.py` | `concurrency` | Bounds strictly enforced | Bounds strictly enforced | `concurrency_validation.json` | PASS |
| Docker-only execution | `docker/gateway_b/Dockerfile` | `compose.yaml` | `execution` | Works in Docker | Works in Docker | `docker_environment.json` | PASS |
| health check | `gateway_b/main.py` | `gateway_b/main.py` | `startup` | Validates Python/OpenSSL | Validates Python/OpenSSL | `docker_environment.json` | PASS |
| security invariants | `gateway_b/transport/protocol.py` | `tests/phase3/runner.py` | `all negative tests` | No unauthorized ingestion | No unauthorized ingestion | `unauthorized_ingestion.json` | PASS |
