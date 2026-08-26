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

## Key Results and Findings

- **TLS-Layer Security Validation:** Client certificate rejections are successfully enforced at the TLS layer, guaranteeing that unauthorized connections consume zero application-layer resources.
- **Fail-Closed Design:** The strict verify-before-decompress ordering proved highly effective. Modified or maliciously crafted compressed payloads are rejected cryptographically before resource-intensive decompression occurs.
- **Identity Assurance:** Sender-ID spoofing scenarios within an established mTLS tunnel are actively neutralized by the identity cross-check mechanism.
- **Concurrency Correctness:** By isolating synchronous operations (like OpenCTI ingestion mocks) within dedicated thread pools, the Gateway B receiver successfully maintains high concurrency without blocking the main event loop.
- **Validation Consistency:** The system consistently produces authoritative, machine-readable JSON evidence matrices validating exact behavior across TLS negative tests, protocol malformations, signature tampering, and policy denials.

## Future Work / Yet to Implement

While the receiving infrastructure and cryptographic baselines are frozen and validated, the following components remain to be implemented in subsequent phases:

- **Phase 4 (Gateway A - Sender):** Implementation of the outbound transmission gateway, responsible for packaging STIX intelligence, applying ML-DSA-65 signatures, compressing payloads, and establishing the outbound mTLS tunnel.
- **Outbound Policy Enforcement (PEP):** Rule engines on the sender side to prevent unauthorized dissemination of sensitive intelligence based on predefined sharing agreements.
- **Live Infrastructure Integration:** Transitioning from the current mock OpenCTI ingestion engine to live, authenticated interactions with active OpenCTI or MISP instances.
- **Advanced Message Queuing:** Implementation of retry logic, dead-letter queues, and resilient transaction states for network disruptions.
- **Production Benchmarking:** Extensive performance evaluation and load testing to measure the latency, throughput, and computational overhead introduced by the post-quantum cryptographic primitives in a high-volume sharing environment.
