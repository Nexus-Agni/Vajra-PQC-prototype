# VAJRA-PQC / QS-TIE - Phase 4 Requirements Traceability Matrix

## Overview
This Traceability Matrix demonstrates the closure of all Phase 4 specifications, mapping requirements to the actual implementation, the test suite, and the machine-readable evidence artifacts. It specifically differentiates between production implementations and mock infrastructure used for testing purposes.

| Req ID | Requirement Description | Type | Implementation Component | Test Coverage (Pytest) | Environment (Real/Mock) | Evidence Artifact | Status |
|---|---|---|---|---|---|---|---|
| 4.1 | Ingestion Subsystem (MISP ZMQ) | REAL | `gateway_a/ingestion/misp_listener.py` | `test_4_1_misp_ingestion.py` | MOCK ZMQ Publisher | `misp_validation.json` | PASS |
| 4.1.1 | Subscribe to ZMQ endpoint | REAL | `misp_listener.py` | `test_misp_listener` | MOCK ZMQ Publisher | `misp_validation.json` | PASS |
| 4.1.2 | Filter by MISP Tags | REAL | `misp_listener.py` | `test_misp_listener` | MOCK ZMQ Publisher | `misp_validation.json` | PASS |
| 4.2 | Payload Extraction & Standardisation | REAL | `gateway_a/ingestion/stix_extractor.py` | `test_4_2_stix_extractor.py` | REAL | `stix_validation.json` | PASS |
| 4.2.1 | Convert MISP JSON to STIX 2.1 | REAL | `stix_extractor.py` | `test_stix_extractor` | REAL | `stix_validation.json` | PASS |
| 4.2.2 | Enforce valid STIX UUIDv4 IDs | REAL | `stix_extractor.py` | `test_stix_extractor` | REAL | `stix_validation.json` | PASS |
| 4.2.3 | Extract TLP Marking | REAL | `stix_extractor.py` | `test_stix_extractor` | REAL | `stix_validation.json` | PASS |
| 4.3 | Compression (Zlib) | REAL | `gateway_a/pipeline/signer_worker.py` | `test_4_3_4_4_compression_signing.py` | REAL | `compression_validation.json` | PASS |
| 4.3.1 | Compress STIX bundle bytes | REAL | `signer_worker.py` | `test_signer_worker` | REAL | `compression_validation.json` | PASS |
| 4.4 | Cryptographic Signing (ML-DSA-65) | REAL | `gateway_a/crypto/signer.py` | `test_4_3_4_4_compression_signing.py` | REAL | `signing_validation.json` | PASS |
| 4.4.1 | Hash payload with SHA-256 | REAL | `signer.py` | `test_ml_dsa_signer` | REAL | `signing_validation.json` | PASS |
| 4.4.2 | Generate ML-DSA-65 signature | REAL | `signer.py` | `test_ml_dsa_signer` | REAL | `signing_validation.json` | PASS |
| 4.5 | Outbound Policy Enforcement (PEP) | REAL | `gateway_a/policy/pep_outbound.py` | `test_4_5_outbound_pep.py` | REAL | `policy_validation.json` | PASS |
| 4.5.1 | Allow configured TLP markings | REAL | `pep_outbound.py` | `test_outbound_pep` | REAL | `policy_validation.json` | PASS |
| 4.5.2 | Deny unconfigured TLP markings | REAL | `pep_outbound.py` | `test_outbound_pep` | REAL | `policy_validation.json` | PASS |
| 4.6 | PQC TLS 1.3 Transport Client | REAL | `gateway_a/crypto/tls_client.py` | `test_4_6_to_4_9_transport.py` | MOCK Dummy Server | `tls_client_validation.json` | PASS |
| 4.6.1 | Enforce TLS 1.3 | REAL | `tls_client.py` | `test_transport_layers` | MOCK Dummy Server | `tls_client_validation.json` | PASS |
| 4.6.2 | Client Certificate Authentication | REAL | `tls_client.py` | `test_transport_layers` | MOCK Dummy Server | `tls_client_validation.json` | PASS |
| 4.6.3 | Reject Wrong Server Cert | REAL | `tls_client.py` | `test_transport_layers` | MOCK Dummy Server | `tls_client_validation.json` | PASS |
| 4.6.4 | Timeout Handling | REAL | `tls_client.py` | `test_transport_layers` | MOCK Dummy Server | `tls_client_validation.json` | PASS |
| 4.7 | Gateway Wire Protocol (Outbound) | REAL | `gateway_a/transport/protocol.py` | `test_4_6_to_4_9_transport.py` | MOCK Dummy Server | `wire_protocol_validation.json` | PASS |
| 4.7.1 | Protocol Framing (1B type, 4B len) | REAL | `protocol.py` | `test_transport_layers` | MOCK Dummy Server | `wire_protocol_validation.json` | PASS |
| 4.7.2 | Serialize TransactionEnvelope | REAL | `protocol.py` | `test_transport_layers` | MOCK Dummy Server | `wire_protocol_validation.json` | PASS |
| 4.8 | Application ACK/NACK Handling | REAL | `gateway_a/pipeline/transmission_worker.py`| `test_4_6_to_4_9_transport.py` | MOCK Dummy Server | `ack_nack_validation.json` | PASS |
| 4.8.1 | Process ACK | REAL | `transmission_worker.py` | `test_transport_layers` | MOCK Dummy Server | `ack_nack_validation.json` | PASS |
| 4.8.2 | Process NACK | REAL | `transmission_worker.py` | `test_transport_layers` | MOCK Dummy Server | `ack_nack_validation.json` | PASS |
| 4.9 | Retries and Exponential Backoff | REAL | `gateway_a/pipeline/transmission_worker.py`| `test_4_6_to_4_9_transport.py` | MOCK Dummy Server | `retry_validation.json` | PASS |
| 4.9.1 | Retry on TLS/Network failures | REAL | `transmission_worker.py` | `test_transport_layers` | MOCK Dummy Server | `retry_validation.json` | PASS |
| 4.9.2 | No retry on NACK failures | REAL | `transmission_worker.py` | `test_transport_layers` | MOCK Dummy Server | `retry_validation.json` | PASS |
| 4.9.3 | Apply backoff (max_attempts=3) | REAL | `transmission_worker.py` | `test_transport_layers` | MOCK Dummy Server | `retry_validation.json` | PASS |
| 4.10 | Dead-Letter Queue (DLQ) | REAL | `gateway_a/pipeline/dead_letter.py` | `test_4_10_4_11_deadletter_metrics.py`| REAL | `deadletter_validation.json` | PASS |
| 4.10.1| Store failed transactions | REAL | `dead_letter.py` | `test_dead_letter_and_metrics`| REAL | `deadletter_validation.json` | PASS |
| 4.10.2| Enforce maxlen=500 | REAL | `dead_letter.py` | `test_dead_letter_and_metrics`| REAL | `deadletter_validation.json` | PASS |
| 4.10.3| Append to JSONL file | REAL | `dead_letter.py` | `test_dead_letter_and_metrics`| REAL | `deadletter_validation.json` | PASS |
| 4.11 | Observability and Metrics | REAL | `gateway_a/observability/metrics.py` | `test_4_10_4_11_deadletter_metrics.py`| REAL | `metrics_validation.json` | PASS |
| 4.11.1| Export via Prometheus HTTP | REAL | `metrics.py` | `test_dead_letter_and_metrics`| REAL | `metrics_validation.json` | PASS |
| 4.12 | End-to-End Orchestration | REAL | `gateway_a/main.py` | `test_4_12_15_integration.py` | REAL Gateway A | `integration_validation.json` | PASS |
| 4.13 | Dockerized Environment | REAL | `docker/gateway_a/Dockerfile` | `repeat_runner.py` | REAL Docker Compose | `repeated_validation.json` | PASS |
| 4.14 | E2E Delivery (Mock MISP -> GW_B) | REAL | `tests/phase4/test_4_12_15_integration.py`| `test_4_12_15_integration.py` | REAL Gateway B | `integration_validation.json` | PASS |
