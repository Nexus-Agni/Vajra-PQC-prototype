import os
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class GatewayAConfig:
    # Identity
    agency_id: str = os.getenv("AGENCY_ID", "RAW")
    cert_path: str = os.getenv("CERT_PATH", "/app/pki/gateway_raw/raw_gateway.crt")
    key_path: str = os.getenv("KEY_PATH", "/app/pki/gateway_raw/raw_gateway.key")
    ml_dsa_private_key_path: str = os.getenv("ML_DSA_PRIVATE_KEY_PATH", "/app/pki/gateway_raw/raw_ml_dsa65.pem")
    ca_trust_path: str = os.getenv("CA_TRUST_PATH", "/app/pki/ca/root_ca.crt")

    # MISP
    misp_zmq_endpoint: str = os.getenv("MISP_ZMQ_ENDPOINT", "tcp://misp-host:50000")
    misp_tags_filter: List[str] = field(default_factory=lambda: os.getenv("MISP_TAGS_FILTER", "share:NIA,tlp:amber").split(","))

    # Network
    hybrid_group: str = os.getenv("HYBRID_GROUP", "X25519MLKEM768")
    
    # Simple static routing for prototype
    recipients: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        "NIA": {"host": os.getenv("GATEWAY_B_HOST", "gateway-b"), "port": os.getenv("GATEWAY_B_PORT", "8443")}
    })

    # Pipeline
    transmission_workers: int = int(os.getenv("TRANSMISSION_WORKERS", "4"))
    ingestion_queue_maxsize: int = int(os.getenv("INGESTION_QUEUE_MAXSIZE", "100"))
    extracted_queue_maxsize: int = int(os.getenv("EXTRACTED_QUEUE_MAXSIZE", "50"))
    signed_queue_maxsize: int = int(os.getenv("SIGNED_QUEUE_MAXSIZE", "50"))
    tx_queue_maxsize: int = int(os.getenv("TX_QUEUE_MAXSIZE", "20"))
    
    # Retry
    max_attempts: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    base_backoff_ms: int = int(os.getenv("BASE_BACKOFF_MS", "200"))
    backoff_factor: int = int(os.getenv("BACKOFF_FACTOR", "2"))

    @classmethod
    def load(cls) -> 'GatewayAConfig':
        return cls()
