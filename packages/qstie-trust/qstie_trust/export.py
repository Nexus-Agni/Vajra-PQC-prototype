import yaml
import os
from typing import List
from qstie_trust.models import TrustBundleEntry

class TrustBundleExporter:
    def __init__(self, entries: List[TrustBundleEntry] = None):
        self.entries = entries or []
        
    def add(self, entry: TrustBundleEntry):
        self.entries.append(entry)
        
    def save(self, filepath: str):
        data = {"trusted_agencies": []}
        for e in self.entries:
            data["trusted_agencies"].append({
                "agency_id": e.agency_id,
                "payload_signing_public_key_path": e.payload_signing_public_key_path,
                "payload_signing_public_key_fingerprint": e.payload_signing_public_key_fingerprint,
                "tls_certificate_fingerprint": e.tls_certificate_fingerprint,
                "issue_timestamp": e.issue_timestamp,
                "expiry_timestamp": e.expiry_timestamp
            })
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
