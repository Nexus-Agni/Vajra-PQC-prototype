import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import mldsa

# Re-use qstie_trust CA tools
from qstie_trust.ca.root_ca import init_root, issue_leaf_cert
from qstie_trust.cli import save_cert, save_private_key

PKI_DIR = "/app/pki"

def main():
    # Load original root CA
    with open(f"{PKI_DIR}/ca/root_ca.crt", "rb") as f:
        root_cert = x509.load_pem_x509_certificate(f.read())
    with open(f"{PKI_DIR}/ca/root_ca.key", "rb") as f:
        root_key = serialization.load_pem_private_key(f.read(), password=None)
        
    class CA:
        cert = root_cert
        private_key = root_key
        
    ca = CA()
    
    # 1. Expired cert
    private_key = mldsa.MLDSA65PrivateKey.generate()
    public_key = private_key.public_key()
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Expired Gateway")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(ca.cert.subject).public_key(public_key).serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(days=10)).not_valid_after(now - datetime.timedelta(days=1)).sign(ca.private_key, None)
    os.makedirs(f"{PKI_DIR}/tls_expired", exist_ok=True)
    save_cert(cert, f"{PKI_DIR}/tls_expired/expired.crt")
    save_private_key(private_key, f"{PKI_DIR}/tls_expired/expired.key")
    
    # 2. Wrong CA cert
    wrong_ca = init_root()
    wrong_cert, wrong_key = issue_leaf_cert(wrong_ca, "WRONG", "wrong-gateway", 90)
    os.makedirs(f"{PKI_DIR}/tls_wrong_ca", exist_ok=True)
    save_cert(wrong_cert, f"{PKI_DIR}/tls_wrong_ca/wrong.crt")
    save_private_key(wrong_key, f"{PKI_DIR}/tls_wrong_ca/wrong.key")

if __name__ == "__main__":
    main()
