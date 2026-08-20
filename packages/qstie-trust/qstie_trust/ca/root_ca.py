import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives.asymmetric import mldsa
from cryptography.hazmat.primitives import serialization

class CertificateAuthority:
    def __init__(self, cert: x509.Certificate, private_key):
        self.cert = cert
        self.private_key = private_key

def init_root(validity_days: int = 3650) -> CertificateAuthority:
    private_key = mldsa.MLDSA65PrivateKey.generate()
    public_key = private_key.public_key()
    
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"QS-TIE Root CA")
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
    ).sign(private_key, None)
    
    return CertificateAuthority(cert, private_key)

def issue_leaf_cert(ca: CertificateAuthority, agency_id: str, san: str, validity_days: int) -> tuple[x509.Certificate, object]:
    private_key = mldsa.MLDSA65PrivateKey.generate()
    public_key = private_key.public_key()
    
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, f"QS-TIE Gateway {agency_id}"),
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
        
    cert = cert_builder.sign(ca.private_key, None)
    
    return cert, private_key
