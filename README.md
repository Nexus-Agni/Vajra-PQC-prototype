# VAJRA-PQC / QS-TIE Prototype Implementation

## Project Overview
The VAJRA-PQC (Post-Quantum Cryptography) / QS-TIE (Quantum-Safe Threat Intelligence Exchange) project is a research prototype designed to integrate post-quantum cryptographic primitives into a secure, federated threat intelligence exchange architecture. The system aims to ensure long-term confidentiality, integrity, and non-repudiation of shared intelligence (such as STIX bundles) against both classical and quantum computing adversaries. 

The architecture is built around a secure communication protocol utilizing TLS 1.3 with hybrid post-quantum key exchange mechanisms and ML-DSA signatures for payload authentication. It encompasses independent gateway modules (Gateway A for sending, Gateway B for receiving) backed by a robust Trust and Key Management Infrastructure.

## Achievements to Date

The prototype has been developed in strict, verifiable phases. The following milestones have been successfully implemented and validated:

### Phase 0: Cryptographic Feasibility
- Established the foundational execution environment requiring Python 3.14.6 and OpenSSL 3.5.7.
- Validated the operational baseline for ML-DSA-65 (payload signing) and X25519MLKEM768 (TLS hybrid key exchange).

### Phase 1: Shared Protocol Contract
- Defined the core protocol serialization using Protocol Buffers.
- Implemented the `TransactionEnvelope` data model.
- Developed a highly resilient framing codec to handle application-layer transactions, including synchronous terminal responses (ACK/NACK) with discrete error reasoning.

### Phase 2: Trust and Key Management Infrastructure
- Developed a complete Public Key Infrastructure (PKI) designed for post-quantum threat intelligence sharing.
- Implemented automated root CA initialization, leaf certificate issuance, and cryptographic key separation.
- Built automated YAML-based trust bundle exports and revocation mechanisms.

### Phase 3: Gateway B (Receiver) Implementation
- Constructed a highly concurrent, connection-driven `asyncio` receiver.
- Implemented an authoritative TLS 1.3 server enforcing mutual TLS (mTLS) client certificate requirements prior to application-layer processing.
- Engineered a deterministic pipeline enforcing a "verify-before-decompress" security ordering. This requires validating the ML-DSA-65 signature over the compressed payload bytes before any decompression occurs, effectively mitigating decompression bomb attacks.
- Implemented an Identity Cross-Check mechanism that cryptographically maps the declared application-layer Sender ID to the authenticated TLS peer certificate fingerprint.
- Developed an Inbound Policy Enforcement Point (PEP) to authorize ingestion based on TLP (Traffic Light Protocol) markings.
- Integrated a `ThreadPoolExecutor` wrapper for synchronous OpenCTI ingestion routines to guarantee the responsiveness of the asynchronous event loop under concurrent load.
- Achieved 100% pass rates across rigorous integration, failure injection, and manual security test matrices within an isolated Docker environment.

### Phase 4: Gateway A (Sender) Implementation
- Constructed an asynchronous pipeline responsible for ingesting MISP events via ZeroMQ, extracting payloads to STIX 2.1, compressing with zlib, and signing with ML-DSA-65.
- Engineered an Outbound Policy Enforcement Point (PEP) to authorize intelligence dissemination based on strict TLP (Traffic Light Protocol) markings.
- Established a PQC hybrid mTLS client (TLS 1.3 with X25519MLKEM768) that orchestrates secure delivery to Gateway B.
- Implemented robust error handling including application-layer ACK/NACK processing, exponential backoff retries for network faults, and a persistent Dead-Letter Queue (bounded deque and JSONL auditing) for terminal failures.
- Embedded a Prometheus HTTP metrics server to expose observability data (queue depths, failure counts, and reasons).
- Successfully completed full, controlled end-to-end integration and rigorous negative testing against Gateway B in Docker, resolving all requirements traceability with zero evidence gaps.

## Key Results and Findings

- **TLS-Layer Security Validation:** Client certificate rejections are successfully enforced at the TLS layer, guaranteeing that unauthorized connections consume zero application-layer resources.
- **Fail-Closed Design:** The strict verify-before-decompress ordering proved highly effective. Modified or maliciously crafted compressed payloads are rejected cryptographically before resource-intensive decompression occurs.
- **Identity Assurance:** Sender-ID spoofing scenarios within an established mTLS tunnel are actively neutralized by the identity cross-check mechanism.
- **Concurrency Correctness:** By isolating synchronous operations (like STIX conversion or OpenCTI ingestion mocks) within dedicated thread pools, both Gateways successfully maintain high concurrency without blocking the main event loop.
- **Resilient Delivery:** Gateway A's pipeline architecture seamlessly handles backpressure, retries transient failures, and safely dead-letters terminally rejected transactions, maintaining strict pipeline stability.
- **Validation Consistency:** The system consistently produces authoritative, machine-readable JSON evidence matrices validating exact behavior across TLS negative tests, protocol malformations, signature tampering, and policy denials.

## Future Work / Yet to Implement

While the core Gateway A/B architecture and cryptographic baselines are frozen and validated, the following components remain to be implemented in subsequent phases:

- **Phase 5 (Full System Integration):** Transitioning from the current mock ingestion and delivery mechanisms (ZMQ mocks and synthetic OpenCTI tokens) to live, authenticated interactions with active MISP and OpenCTI instances.
- **Production Benchmarking:** Extensive performance evaluation and load testing to measure the latency, throughput, and computational overhead introduced by the post-quantum cryptographic primitives in a high-volume sharing environment.
- **Advanced Orchestration:** Deployment configurations for Kubernetes or Swarm to evaluate scalability and high availability of the gateway services.
