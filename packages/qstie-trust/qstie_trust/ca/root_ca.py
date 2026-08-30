import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives.asymmetric import mldsa, ec
from cryptography.hazmat.primitives import hashes

class CertificateAuthority:
    def __init__(self, cert: x509.Certificate, private_key):
        self.cert = cert
        self.private_key = private_key

def init_root(validity_days: int = 3650, key_type: str = "mldsa") -> CertificateAuthority:
    if key_type == "ecdsa":
        private_key = ec.generate_private_key(ec.SECP256R1())
        alg = hashes.SHA256()
    else:
        private_key = mldsa.MLDSA65PrivateKey.generate()
        alg = None
        
    public_key = private_key.public_key()
    
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, f"QS-TIE Root CA ({key_type})")
    ])
    
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        public_key
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        now
    ).not_valid_after(
        now + datetime.timedelta(days=validity_days)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True,
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=True,
            encipher_only=False,
            decipher_only=False,
        ), critical=True
    ).sign(private_key, alg)
    
    return CertificateAuthority(cert, private_key)

def issue_leaf_cert(ca: CertificateAuthority, agency_id: str, san: str, validity_days: int, key_type: str = "mldsa") -> tuple[x509.Certificate, object]:
    if key_type == "ecdsa":
        private_key = ec.generate_private_key(ec.SECP256R1())
    else:
        private_key = mldsa.MLDSA65PrivateKey.generate()
        
    public_key = private_key.public_key()
    
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, f"QS-TIE Gateway {agency_id} ({key_type})"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, agency_id)
    ])
    
    now = datetime.datetime.now(datetime.timezone.utc)
    
    cert_builder = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca.cert.subject
    ).public_key(
        public_key
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        now
    ).not_valid_after(
        now + datetime.timedelta(days=validity_days)
    ).add_extension(
        x509.BasicConstraints(ca=False, path_length=None), critical=True,
    )
    
    if san:
        cert_builder = cert_builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(san)]), critical=False,
        )
        
    if isinstance(ca.private_key, ec.EllipticCurvePrivateKey):
        alg = hashes.SHA256()
    else:
        alg = None
        
    cert = cert_builder.sign(ca.private_key, alg)
    
    return cert, private_key
