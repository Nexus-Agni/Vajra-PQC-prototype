import pytest
import asyncio
from gateway_b.config import GatewayConfig
from gateway_b.trust.cert_store import TrustStore
from gateway_b.crypto.verifier import MLDSAVerifier
from gateway_b.policy.pep_inbound import InboundPEP
from gateway_b.ingestion.stix_ingestor import OpenCTIIngestor
from gateway_b.transport.protocol import GatewayProtocol
from gateway_b.transport.tls_server import TLSServer
import ssl
import threading

@pytest.fixture(scope="session")
def pki_dir():
    return "/app/pki"

@pytest.fixture
async def gateway_server(pki_dir):
    config = GatewayConfig()
    config.listen_port = 8443
    config.cert_path = f"{pki_dir}/gateway_nia/nia_gateway.crt"
    config.key_path = f"{pki_dir}/gateway_nia/nia_gateway.key"
    config.ca_trust_path = f"{pki_dir}/ca/root_ca.crt"
    config.trust_store_path = f"{pki_dir}/trust_store.yaml"
    config.revocation_list_path = f"{pki_dir}/revocation_list.yaml"
    
    trust_store = TrustStore(config.trust_store_path, config.revocation_list_path)
    verifier = MLDSAVerifier(pki_dir)
    
    rules = [
        {"sender": "RAW", "recipient": "NIA", "tlp": "tlp:green", "action": "ALLOW"},
        {"sender": "RAW", "recipient": "NIA", "tlp": "tlp:amber", "action": "ALLOW"},
        {"sender": "RAW", "recipient": "NIA", "tlp": "tlp:amber+strict", "action": "DENY"}
    ]
    pep = InboundPEP(rules)
    ingestor = OpenCTIIngestor("mock", "mock", 4)
    protocol_handler = GatewayProtocol(trust_store, verifier, pep, ingestor)
    
    server = TLSServer(
        host="127.0.0.1",
        port=config.listen_port,
        cert_path=config.cert_path,
        key_path=config.key_path,
        ca_trust_path=config.ca_trust_path,
        hybrid_group=config.hybrid_group,
        max_concurrent=10,
        protocol_handler=protocol_handler
    )
    
    # We will start it in the event loop as a task
    server_task = asyncio.create_task(server.start())
    
    # Wait for server to start
    await asyncio.sleep(0.1)
    
    # Yield the components for inspection
    yield {
        "server": server,
        "task": server_task,
        "ingestor": ingestor,
        "port": config.listen_port,
        "pki_dir": pki_dir
    }
    
    server_task.cancel()
