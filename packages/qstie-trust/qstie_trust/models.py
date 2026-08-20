from dataclasses import dataclass
from typing import Optional

@dataclass
class TrustBundleEntry:
    agency_id: str
    payload_signing_public_key_path: str
    payload_signing_public_key_fingerprint: str
    tls_certificate_fingerprint: str
    issue_timestamp: str
    expiry_timestamp: str

@dataclass
class RevocationEntry:
    fingerprint: str
    key_type: str
    agency_id: str
    reason: str
    revoked_at: str

@dataclass
class CertMetadata:
    agency_id: str
    subject: str
    issuer: str
    san: Optional[str]
    serial_number: str
    algorithm: str
    valid_from: str
    valid_until: str
    fingerprint: str
    key_type: str
