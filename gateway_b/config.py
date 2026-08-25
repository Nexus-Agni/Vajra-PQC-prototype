import os
import yaml
from dataclasses import dataclass

@dataclass
class GatewayConfig:
    # Network
    listen_host: str = os.getenv("LISTEN_HOST", "0.0.0.0")
    listen_port: int = int(os.getenv("LISTEN_PORT", "8443"))
    max_concurrent_connections: int = int(os.getenv("MAX_CONCURRENT_CONNECTIONS", "10"))
    hybrid_group: str = os.getenv("HYBRID_GROUP", "X25519MLKEM768")

    # Identity
    agency_id: str = os.getenv("AGENCY_ID", "NIA")
    cert_path: str = os.getenv("CERT_PATH", "/app/pki/gateway_nia/nia_gateway.crt")
    key_path: str = os.getenv("KEY_PATH", "/app/pki/gateway_nia/nia_gateway.key")
    ca_trust_path: str = os.getenv("CA_TRUST_PATH", "/app/pki/ca/root_ca.crt")

    # Trust
    trust_store_path: str = os.getenv("TRUST_STORE_PATH", "/app/pki/trust_store.yaml")
    revocation_list_path: str = os.getenv("REVOCATION_LIST_PATH", "/app/pki/revocation_list.yaml")

    # OpenCTI
    opencti_url: str = os.getenv("OPENCTI_URL", "http://opencti:8080")
    opencti_token: str = os.getenv("OPENCTI_API_TOKEN", "")
    executor_workers: int = int(os.getenv("EXECUTOR_WORKERS", "4"))
    
    @classmethod
    def load(cls) -> 'GatewayConfig':
        # Extend to load from a yaml file if needed, currently relies on ENV vars
        return cls()
