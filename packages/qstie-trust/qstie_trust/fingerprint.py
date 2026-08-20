from qstie_common.fingerprints.utils import calculate_fingerprint
import hashlib
from cryptography.hazmat.primitives import serialization
from cryptography import x509

def get_cert_fingerprint(cert: x509.Certificate) -> str:
    # Use DER bytes for standard representation
    der_bytes = cert.public_bytes(serialization.Encoding.DER)
    return calculate_fingerprint(der_bytes)

def get_pubkey_fingerprint(pubkey) -> str:
    # Use SubjectPublicKeyInfo (SPKI) DER bytes
    der_bytes = pubkey.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return calculate_fingerprint(der_bytes)
