import os
import yaml
from dataclasses import dataclass
from typing import Dict, Optional, List

class TrustStore:
    def __init__(self, trust_store_path: str, revocation_list_path: str):
        self.trust_store_path = trust_store_path
        self.revocation_list_path = revocation_list_path
        self.pki_base_dir = os.path.dirname(trust_store_path)
        
        self.agencies: Dict[str, dict] = {}
        self.revoked_fingerprints: set[str] = set()
        
        self.load()

    def load(self):
        with open(self.trust_store_path, 'r') as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict) or 'trusted_agencies' not in data:
                raise ValueError("Invalid trust store format")
            for agency in data.get('trusted_agencies', []):
                self.agencies[agency['agency_id']] = agency

        try:
            with open(self.revocation_list_path, 'r') as f:
                rev_data = yaml.safe_load(f)
                if rev_data and 'revoked_certificates' in rev_data:
                    for cert in rev_data['revoked_certificates']:
                        self.revoked_fingerprints.add(cert['fingerprint'])
        except FileNotFoundError:
            raise FileNotFoundError("Revocation list missing")
            
    def get_agency(self, agency_id: str) -> Optional[dict]:
        return self.agencies.get(agency_id)

    def is_revoked(self, fingerprint: str) -> bool:
        return fingerprint in self.revoked_fingerprints
