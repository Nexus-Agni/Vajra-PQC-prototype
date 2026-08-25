import asyncio
import logging
import sys
from gateway_b.config import GatewayConfig
from gateway_b.trust.cert_store import TrustStore
from gateway_b.crypto.verifier import MLDSAVerifier
from gateway_b.policy.pep_inbound import InboundPEP
from gateway_b.ingestion.stix_ingestor import OpenCTIIngestor
from gateway_b.transport.protocol import GatewayProtocol
from gateway_b.transport.tls_server import TLSServer
import ssl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_phase0_baseline():
    # Python 3.14.6
    if sys.version_info[:3] != (3, 14, 6):
        logger.error("PHASE 0 BASELINE REGRESSION / ENVIRONMENT DRIFT: Python 3.14.6 required")
        sys.exit(1)
        
    # OpenSSL 3.5.7
    if "3.5.7" not in ssl.OPENSSL_VERSION:
        logger.error("PHASE 0 BASELINE REGRESSION / ENVIRONMENT DRIFT: OpenSSL 3.5.7 required")
        sys.exit(1)
        
    # Checking for ML-DSA-65 capability
    try:
        from cryptography.hazmat.primitives.asymmetric import mldsa
        _ = mldsa.MLDSA65PrivateKey.generate()
    except Exception:
        logger.error("PHASE 0 BASELINE REGRESSION / ENVIRONMENT DRIFT: ML-DSA-65 missing")
        sys.exit(1)

async def main():
    check_phase0_baseline()
    
    config = GatewayConfig.load()
    
    try:
        trust_store = TrustStore(config.trust_store_path, config.revocation_list_path)
    except Exception as e:
        logger.error(f"PHASE 0 BASELINE REGRESSION / ENVIRONMENT DRIFT: Trust artifacts error: {e}")
        sys.exit(1)
        
    verifier = MLDSAVerifier("/app/pki")
    
    # Example rules for Phase 3
    rules = [
        {"sender": "RAW", "recipient": "NIA", "tlp": "tlp:green", "action": "ALLOW"},
        {"sender": "RAW", "recipient": "NIA", "tlp": "tlp:amber", "action": "ALLOW"},
        {"sender": "RAW", "recipient": "NIA", "tlp": "tlp:amber+strict", "action": "DENY"}
    ]
    pep = InboundPEP(rules)
    
    ingestor = OpenCTIIngestor(config.opencti_url, config.opencti_token, config.executor_workers)
    
    protocol_handler = GatewayProtocol(trust_store, verifier, pep, ingestor)
    
    server = TLSServer(
        host=config.listen_host,
        port=config.listen_port,
        cert_path=config.cert_path,
        key_path=config.key_path,
        ca_trust_path=config.ca_trust_path,
        hybrid_group=config.hybrid_group,
        max_concurrent=config.max_concurrent_connections,
        protocol_handler=protocol_handler
    )
    
    await server.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
