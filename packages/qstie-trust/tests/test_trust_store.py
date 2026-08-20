import os
import pytest
import yaml
from cryptography.hazmat.primitives import serialization
from qstie_trust.fingerprint import get_cert_fingerprint, get_pubkey_fingerprint
from qstie_trust.cli import load_cert, load_private_key

PKI_DIR = "/app/pki"

def load_trust_store():
    with open(f"{PKI_DIR}/trust_store.yaml", 'r') as f:
        return yaml.safe_load(f)

def test_trust_store_no_private_keys():
    # Verify trust store contains no private material
    with open(f"{PKI_DIR}/trust_store.yaml", 'r') as f:
        content = f.read()
    assert "PRIVATE KEY" not in content
    assert "root_ca.key" not in content
    assert "raw_gateway.key" not in content

def test_trust_store_known_senders():
    store = load_trust_store()
    agencies = {e["agency_id"]: e for e in store["trusted_agencies"]}
    assert "RAW" in agencies
    assert "NIA" in agencies

def test_trust_store_reject_unknown_sender():
    store = load_trust_store()
    agencies = [e["agency_id"] for e in store["trusted_agencies"]]
    assert "UNKNOWN" not in agencies

def test_trust_store_fingerprints_match():
    store = load_trust_store()
    agencies = {e["agency_id"]: e for e in store["trusted_agencies"]}
    
    # Check RAW
    raw_cert = load_cert(f"{PKI_DIR}/gateway_raw/raw_gateway.crt")
    raw_payload_pub = load_private_key(f"{PKI_DIR}/gateway_raw/raw_ml_dsa65.pem").public_key()
    
    assert agencies["RAW"]["tls_certificate_fingerprint"] == get_cert_fingerprint(raw_cert)
    assert agencies["RAW"]["payload_signing_public_key_fingerprint"] == get_pubkey_fingerprint(raw_payload_pub)
    
    # Check NIA
    nia_cert = load_cert(f"{PKI_DIR}/gateway_nia/nia_gateway.crt")
    nia_payload_pub = load_private_key(f"{PKI_DIR}/gateway_nia/nia_ml_dsa65.pem").public_key()
    
    assert agencies["NIA"]["tls_certificate_fingerprint"] == get_cert_fingerprint(nia_cert)
    assert agencies["NIA"]["payload_signing_public_key_fingerprint"] == get_pubkey_fingerprint(nia_payload_pub)

def test_trust_store_malformed():
    with open(f"{PKI_DIR}/trust_store_malformed.yaml", 'w') as f:
        f.write("trusted_agencies: [ {")
        
    with pytest.raises(yaml.YAMLError):
        with open(f"{PKI_DIR}/trust_store_malformed.yaml", 'r') as f:
            yaml.safe_load(f)

def test_trust_store_missing():
    assert not os.path.exists(f"{PKI_DIR}/nonexistent_trust_store.yaml")
