import os
import pytest
import yaml
from qstie_trust.ca.revocation import RevocationList
from qstie_trust.cli import load_cert
from qstie_trust.fingerprint import get_cert_fingerprint

PKI_DIR = "/app/pki"

def test_revocation_startup_only():
    import shutil
    shutil.copy(f"{PKI_DIR}/revocation_list.yaml", f"{PKI_DIR}/revocation_list_test.yaml")
    
    rl = RevocationList.load(f"{PKI_DIR}/revocation_list_test.yaml")
    initial_count = len(rl.entries)
    
    # modify file
    with open(f"{PKI_DIR}/revocation_list_test.yaml", 'a') as f:
        f.write("\n  - fingerprint: 'test'\n    key_type: 'test'\n    agency_id: 'test'\n    reason: 'test'\n    revoked_at: 'test'\n")
        
    # The running object does not update automatically
    assert len(rl.entries) == initial_count

def test_revocation_revoked_cert():
    rl = RevocationList.load(f"{PKI_DIR}/revocation_list.yaml")
    revoked_fps = [e.fingerprint for e in rl.entries]
    
    cert = load_cert(f"{PKI_DIR}/gateway_raw/raw_gateway.crt")
    fp = get_cert_fingerprint(cert)
    
    # Ensure it's rejected
    assert fp in revoked_fps

def test_revocation_non_revoked_cert():
    rl = RevocationList.load(f"{PKI_DIR}/revocation_list.yaml")
    revoked_fps = [e.fingerprint for e in rl.entries]
    
    cert = load_cert(f"{PKI_DIR}/gateway_nia/nia_gateway.crt")
    fp = get_cert_fingerprint(cert)
    
    # Ensure it's accepted
    assert fp not in revoked_fps

def test_revocation_invalid_fingerprint():
    rl = RevocationList.load(f"{PKI_DIR}/revocation_list.yaml")
    revoked_fps = [e.fingerprint for e in rl.entries]
    assert "invalid_fp_format!@#" not in revoked_fps

def test_revocation_malformed():
    with open(f"{PKI_DIR}/revocation_list_malformed.yaml", 'w') as f:
        f.write("revoked: [ {")
        
    with pytest.raises(Exception):
        RevocationList.load(f"{PKI_DIR}/revocation_list_malformed.yaml")
