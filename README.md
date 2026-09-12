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

### Phase 5: Production Benchmarking Framework
- Developed an automated benchmarking suite to evaluate Post-Quantum (ML-DSA / ML-KEM) versus Classical (X25519) cryptographic overhead.
- Configured Linux `tc` (Traffic Control) to emulate stable loopback and adverse tactical networks (50ms delay, 3% packet loss, 5Mbps bandwidth limit).
- Established baseline latency, throughput, and error metrics across both configurations.

### Phase 6: Full System Integration
- Transitioned from mock data generators to live, authenticated interactions with active MISP and OpenCTI instances.
- Replaced synthetic tokens with real API credential management.
- Successfully verified end-to-end tactical intelligence flow from a live MISP generator, through the PQC-secured gateways, to final OpenCTI ingestion.

### Phase 7: Empirical PQC Profiling & Queueing Dynamics
- Conducted a robust, 5,000-event empirical re-analysis of the benchmark data.
- Leveraged Non-parametric Cluster Bootstrapping (1,000 resamples) to generate statistically defensible Confidence Intervals that account for queue-state correlation.
- Decomposed latency to prove that "Crypto-Path" delays are heavily dominated by thread-pool parallelization limits (queueing) and TCP window scaling during packet loss, rather than raw CPU signing time (which remains ~1.17 ms).
- Conclusively proved the primary thesis: Under adverse tactical environments, environmental noise entirely masks the computational overhead introduced by Hybrid PQC algorithms.

## Key Results and Findings

- **Cryptographic Overhead is Masked by Noise:** In tactical environments (3% packet loss, 50ms delay), true end-to-end latency skyrockets to ~164 seconds for both Classical and PQC suites due to TCP stalling and retransmissions. The PQC overhead is statistically negligible in the face of environmental noise.
- **Thread-Pool Queueing Limits:** Performance ceilings in stable conditions (~7.1-7.4 seconds end-to-end) are driven by concurrent signing queue backups, not CPU bottlenecks.
- **TLS-Layer Security Validation:** Client certificate rejections are successfully enforced at the TLS layer, guaranteeing that unauthorized connections consume zero application-layer resources.
- **Fail-Closed Design:** The strict verify-before-decompress ordering proved highly effective. Modified or maliciously crafted compressed payloads are rejected cryptographically before resource-intensive decompression occurs.
- **Identity Assurance:** Sender-ID spoofing scenarios within an established mTLS tunnel are actively neutralized by the identity cross-check mechanism.

## Future Work / Yet to Implement

While the core Gateway architecture, live integrations, and empirical benchmarking are successfully validated, the following components remain for future expansion:

- **Advanced Orchestration:** Deployment configurations for Kubernetes or Helm to evaluate dynamic scalability, horizontal pod autoscaling, and high availability of the gateway services under production loads.
