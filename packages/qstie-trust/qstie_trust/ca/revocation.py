import yaml
import os
from typing import List, Dict
from qstie_trust.models import RevocationEntry

class RevocationList:
    def __init__(self, entries: List[RevocationEntry] = None):
        self.entries = entries or []
        
    def add(self, entry: RevocationEntry):
        self.entries.append(entry)
        
    def save(self, filepath: str):
        data = {"revoked": []}
        for e in self.entries:
            data["revoked"].append({
                "fingerprint": e.fingerprint,
                "key_type": e.key_type,
                "agency_id": e.agency_id,
                "reason": e.reason,
                "revoked_at": e.revoked_at
            })
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
            
    @classmethod
    def load(cls, filepath: str) -> 'RevocationList':
        if not os.path.exists(filepath):
            return cls()
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
            
        entries = []
        if data and "revoked" in data:
            for item in data["revoked"]:
                entries.append(RevocationEntry(**item))
        return cls(entries)
