# Phase 2 Requirements Traceability

| Requirement | Implementation file | Test file | Test name | Expected result | Actual result | Evidence artifact | Status |
|---|---|---|---|---|---|---|---|
| Root CA | ca/root_ca.py | test_pki.py | test_root_ca_generation | CA cert generated | CA cert generated | certificate_metadata.json | PASS |
| Root CA Validity | ca/root_ca.py | test_pki.py | test_root_ca_generation | Self-signed | Self-signed | certificate_metadata.json | PASS |
| Root CA Isolation | ca/root_ca.py | test_security.py | test_root_ca_isolation | Not in GW dir | Not in GW dir | file_permissions.json | PASS |
| Gateway A Cert | ca/root_ca.py | test_pki.py | test_leaf_cert_generation | Cert generated | Cert generated | certificate_metadata.json | PASS |
| Gateway B Cert | ca/root_ca.py | test_pki.py | test_leaf_cert_generation | Cert generated | Cert generated | certificate_metadata.json | PASS |
| Cert Validity | ca/root_ca.py | test_security.py | test_expired_certificate | Expired detected | Expired detected | test execution | PASS |
| Cert SAN | ca/root_ca.py | test_security.py | test_wrong_san | Wrong SAN detected | Wrong SAN detected | certificate_metadata.json | PASS |
| Cert/Key Match | ca/root_ca.py | test_pki.py | test_cert_key_mismatch | Mismatch detected | Mismatch detected | test execution | PASS |
| Signing Keys | ca/signing_keygen.py | test_cli.py | test_cli_issue_signing_key | Keys generated | Keys generated | test execution | PASS |
| Key Separation | ca/signing_keygen.py | test_security.py | test_key_separation_cross_usage | Use fails | Use fails | key_separation.json | PASS |
| Trust Bundle | export.py | test_trust_store.py | test_trust_store_known_senders | Bundle generated | Bundle generated | test execution | PASS |
| Trust Public-Only | export.py | test_trust_store.py | test_trust_store_no_private_keys | No private keys | No private keys | test execution | PASS |
| Revocation | ca/revocation.py | test_revocation.py | test_revocation_startup_only | List generated | List generated | revocation_validation.json | PASS |
| Private Key Perms | cli.py | test_security.py | test_file_permissions | 0600 perms | 0600 perms | file_permissions.json | PASS |
| CLI Tests | cli.py | test_cli.py | all | Success | Success | test execution | PASS |
| Bootstrap | scripts/bootstrap_pki.py | N/A | N/A | Exits 0 | Exits 0 | bootstrap_runs.json | PASS |
| Clean Bootstrap | scripts/bootstrap_pki.py | N/A | N/A | Success | Success | bootstrap_runs.json | PASS |
| Repeated Bootstrap | scripts/bootstrap_pki.py | N/A | N/A | Success 2 times | Success 2 times | bootstrap_runs.json | PASS |
| Docker-only Execution | compose.yaml | N/A | N/A | Only runs in docker | Runs in docker | bootstrap_runs.json | PASS |
