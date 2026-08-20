import os
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import mldsa
from qstie_trust.ca.root_ca import init_root, issue_leaf_cert, CertificateAuthority
from qstie_trust.ca.signing_keygen import generate_ml_dsa_keypair
from qstie_trust.fingerprint import get_cert_fingerprint, get_pubkey_fingerprint

def test_root_ca_generation():
    ca = init_root(validity_days=3650)
    assert ca.cert is not None
    assert ca.private_key is not None
    assert isinstance(ca.private_key, mldsa.MLDSA65PrivateKey)
    
    # Check self signed
    assert ca.cert.issuer == ca.cert.subject
    
    # Verify signature
    ca.private_key.public_key().verify(
        ca.cert.signature,
        ca.cert.tbs_certificate_bytes,
        None
    )

def test_leaf_cert_generation():
    ca = init_root(365)
    leaf_cert, leaf_key = issue_leaf_cert(ca, "RAW", "gateway-a.internal", 90)
    
    assert leaf_cert.issuer == ca.cert.subject
    assert "RAW" in leaf_cert.subject.rfc4514_string()
    
    # Verify chain
    ca.private_key.public_key().verify(
        leaf_cert.signature,
        leaf_cert.tbs_certificate_bytes,
        None
    )
    
    # Check ML-DSA-65
    assert isinstance(leaf_key, mldsa.MLDSA65PrivateKey)

def test_key_separation():
    ca = init_root()
    leaf_cert, tls_key = issue_leaf_cert(ca, "RAW", "gateway-a.internal", 90)
    payload_priv, payload_pub = generate_ml_dsa_keypair()
    
    tls_pub_fp = get_pubkey_fingerprint(tls_key.public_key())
    payload_pub_fp = get_pubkey_fingerprint(payload_pub)
    
    assert tls_pub_fp != payload_pub_fp

def test_cert_key_mismatch():
    ca = init_root()
    cert_a, key_a = issue_leaf_cert(ca, "RAW", "gateway-a", 90)
    cert_b, key_b = issue_leaf_cert(ca, "NIA", "gateway-b", 90)
    
    # Match
    pub_fp_a_from_cert = get_pubkey_fingerprint(cert_a.public_key())
    pub_fp_a_from_key = get_pubkey_fingerprint(key_a.public_key())
    assert pub_fp_a_from_cert == pub_fp_a_from_key
    
    pub_fp_b_from_key = get_pubkey_fingerprint(key_b.public_key())
    assert pub_fp_a_from_cert != pub_fp_b_from_key
