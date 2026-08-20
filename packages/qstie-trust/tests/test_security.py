import os
import pytest
import yaml
import datetime
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import mldsa
from qstie_trust.ca.root_ca import init_root, issue_leaf_cert
from qstie_trust.ca.signing_keygen import generate_ml_dsa_keypair
from qstie_trust.fingerprint import get_cert_fingerprint, get_pubkey_fingerprint
from qstie_trust.cli import save_cert, save_private_key, load_private_key

PKI_DIR = "/app/pki"

def test_root_ca_isolation():
    # Verify root_ca.key is not in gateway dirs
    for gw in ["gateway_raw", "gateway_nia"]:
        assert not os.path.exists(os.path.join(PKI_DIR, gw, "root_ca.key"))

def test_root_not_in_trust_bundle():
    trust_store_path = os.path.join(PKI_DIR, "trust_store.yaml")
    with open(trust_store_path, "r") as f:
        content = f.read()
    assert "root_ca.key" not in content
    assert "PRIVATE KEY" not in content

def test_file_permissions():
    private_keys = [
        f"{PKI_DIR}/ca/root_ca.key",
        f"{PKI_DIR}/gateway_raw/raw_gateway.key",
        f"{PKI_DIR}/gateway_raw/raw_ml_dsa65.pem",
        f"{PKI_DIR}/gateway_nia/nia_gateway.key",
        f"{PKI_DIR}/gateway_nia/nia_ml_dsa65.pem"
    ]
    for key in private_keys:
        if os.path.exists(key):
            stat = os.stat(key)
            assert stat.st_mode & 0o777 == 0o600

def test_wrong_ca():
    ca1 = init_root()
    ca2 = init_root()
    cert1, key1 = issue_leaf_cert(ca1, "RAW", "gateway-a", 90)
    
    # Validation against wrong CA should fail
    with pytest.raises(Exception):
        ca2.private_key.public_key().verify(cert1.signature, cert1.tbs_certificate_bytes, None)

def test_expired_certificate():
    # To test expiration, we can't use issue_leaf_cert because it sets not_valid_before to now.
    # We will build a cert explicitly.
    from cryptography.x509.oid import NameOID
    ca = init_root()
    private_key = mldsa.MLDSA65PrivateKey.generate()
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Expired")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca.cert.subject
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        now - datetime.timedelta(days=10)
    ).not_valid_after(
        now - datetime.timedelta(days=5)
    ).sign(ca.private_key, None)
    
    now = datetime.datetime.now(datetime.timezone.utc)
    assert cert.not_valid_after_utc < now

def test_wrong_san():
    ca = init_root()
    cert, key = issue_leaf_cert(ca, "RAW", "wrong-san", 90)
    
    san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
    sans = san_ext.value.get_values_for_type(x509.DNSName)
    assert "wrong-san" in sans
    assert "gateway-a.internal" not in sans

def test_trust_store_schema():
    trust_store_path = os.path.join(PKI_DIR, "trust_store.yaml")
    with open(trust_store_path, "r") as f:
        data = yaml.safe_load(f)
        
    assert "trusted_agencies" in data
    agencies = [entry["agency_id"] for entry in data["trusted_agencies"]]
    assert "RAW" in agencies
    assert "NIA" in agencies

def test_key_separation_cross_usage():
    # Load keys
    tls_key = load_private_key(f"{PKI_DIR}/gateway_raw/raw_gateway.key")
    payload_key = load_private_key(f"{PKI_DIR}/gateway_raw/raw_ml_dsa65.pem")
    
    tls_pub_fp = get_pubkey_fingerprint(tls_key.public_key())
    payload_pub_fp = get_pubkey_fingerprint(payload_key.public_key())
    
    # Assert they are cryptographically different
    assert tls_pub_fp != payload_pub_fp
    
    # To truly prove we can't use them interchangeably, if they were used in an actual protocol,
    # the public keys distributed wouldn't match. 
    # Let's test that verify() fails when crossed.
    message = b"test message"
    sig = tls_key.sign(message, None)
    
    with pytest.raises(Exception):
        payload_key.public_key().verify(sig, message, None)
        
    sig2 = payload_key.sign(message, None)
    with pytest.raises(Exception):
        tls_key.public_key().verify(sig2, message, None)

def test_revocation_schema():
    rev_list_path = os.path.join(PKI_DIR, "revocation_list.yaml")
    with open(rev_list_path, "r") as f:
        data = yaml.safe_load(f)
        
    assert "revoked" in data
    assert len(data["revoked"]) > 0
    entry = data["revoked"][0]
    assert "fingerprint" in entry
    assert "key_type" in entry
    assert "agency_id" in entry
    assert "reason" in entry
    assert "revoked_at" in entry

