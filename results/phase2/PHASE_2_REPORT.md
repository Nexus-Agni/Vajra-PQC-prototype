# PHASE 2 — TRUST & KEY BOOTSTRAP VALIDATION REPORT

## 1. Phase Objective
Build the complete OFFLINE trust and key-management infrastructure.

## 2. Phase Scope
- qstie-trust shared package
- qstie-ca CLI
- Root CA generation
- Gateway leaf certificate issuance
- Payload-signing key generation
- Trust bundle and revocation list generation
- qstie-ca-bootstrap Docker image/container
- Security tests & Validation

## 3. Repository Baseline
git commit: 1ed2505ab9fdcad2f43f3689de9f2fb7659e66c4
branch: phase-2
working tree state: clean

## 4. Docker Environment
Docker version: Docker version 24.0.2
image: docker.io/library/prototype-implementation-main-qstie-ca-bootstrap:latest
Python version: 3.14.6
OpenSSL version: OpenSSL 3.5.7 9 Jun 2026
OS: Linux (debian slim)

## 5. Implementation Summary
qstie-trust package implemented.
qstie-ca CLI tool created.
Root CA generated successfully using ML-DSA-65.
TLS certificates generated for Gateway A and B.
Payload signing keys generated for Gateway A and B.
Trust bundle schema implemented.
Revocation list schema implemented.
Bootstrap container executed correctly.

## 6. PKI Artifact Inventory
pki/ca/root_ca.crt - PUBLIC TRUST
pki/ca/root_ca.key - OFFLINE PRIVATE
pki/gateway_raw/raw_gateway.crt - GATEWAY PUBLIC
pki/gateway_raw/raw_gateway.key - GATEWAY PRIVATE
pki/gateway_raw/raw_ml_dsa65.pem - GATEWAY PRIVATE
pki/gateway_raw/raw_ml_dsa65.pub - PUBLIC TRUST
pki/gateway_nia/nia_gateway.crt - GATEWAY PUBLIC
pki/gateway_nia/nia_gateway.key - GATEWAY PRIVATE
pki/gateway_nia/nia_ml_dsa65.pem - GATEWAY PRIVATE
pki/gateway_nia/nia_ml_dsa65.pub - PUBLIC TRUST
pki/trust_store.yaml - METADATA / PUBLIC TRUST
pki/revocation_list.yaml - METADATA / PUBLIC TRUST

## 7. Root CA Validation
PASS

## 8. Gateway Certificate Validation
Gateway A:
PASS

Gateway B:
PASS

## 9. Payload Signing Key Validation
RAW:
PASS

NIA:
PASS

## 10. Key Separation
RAW:
PASS

NIA:
PASS

## 11. Trust Bundle
PASS

## 12. Revocation
PASS

## 13. File Permissions
PASS

## 14. CLI Tests
7/7

## 15. Security Tests
9/9

## 16. Certificate Tests
4/4

## 17. Trust-Store Tests
6/6

## 18. Revocation Tests
5/5

## 19. Docker Tests
1/1

## 20. Reproducibility Tests
2/2

## 21. Clean Bootstrap
PASS

## 22. Bootstrap Run Evidence
run-1: SUCCESS, exit status 0
run-2: SUCCESS, exit status 0

## 23. Evidence Generated
results/phase2/evidence/certificate_metadata.json
results/phase2/evidence/key_separation.json
results/phase2/evidence/revocation_validation.json
results/phase2/evidence/file_permissions.json
results/phase2/evidence/bootstrap_runs.json

## 24. Requirements Traceability
PASS

## 25. Important Findings
- The offline bootstrap container cleanly ran in a one-shot execution, generated the required static artifacts, executed the validation tests, and securely exited.
- Python 3.14.6 and OpenSSL 3.5.7 natively generated the required ML-DSA-65 keys and X.509 certificates cleanly using `cryptography` primitives, confirming the environmental baseline feasibility.

## 26. Thesis-Relevant Findings
Observation: The Phase-2 bootstrap successfully generated an ML-DSA-65 root and independent ML-DSA-65 gateway identities.
Evidence: results/phase2/evidence/certificate_metadata.json
Interpretation: Cryptographic agility utilizing ML-DSA-65 is feasible using standard X.509 constructs in the validated Phase 0 baseline environment.
Limitation: Certificates are simulated offline; no HSM interaction.

Observation: TLS and payload-signing private keys are structurally and cryptographically separated.
Evidence: results/phase2/evidence/key_separation.json, test_key_separation_cross_usage
Interpretation: Separation of concerns minimizes the risk of cross-protocol attacks or key compromise spanning multiple layers.
Limitation: Does not evaluate runtime usage in Gateway A/B.

## 27. Known Issues
None.

## 28. Limitations
- offline simulated CA;
- no HSM;
- no automated enrollment;
- startup-only revocation;
- no live OCSP/CRL;
- synthetic environment.

## 29. Blockers
None.

## 30. Final Gate Decision
GO
