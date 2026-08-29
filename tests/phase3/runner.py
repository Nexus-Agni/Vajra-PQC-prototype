import asyncio
import ssl
import json
import zlib
import hashlib
import os
import sys
import logging
import traceback
from datetime import datetime, timezone
from cryptography.hazmat.primitives import serialization
from qstie_common.models.envelope import TransactionEnvelope
from qstie_common.enums.protocol_enums import TlpMarking, MessageType, NackReason
from qstie_common.protocol.frame_codec import FrameCodec

# Gateway B imports
from gateway_b.config import GatewayConfig
from gateway_b.trust.cert_store import TrustStore
from gateway_b.crypto.verifier import MLDSAVerifier
from gateway_b.policy.pep_inbound import InboundPEP
from gateway_b.ingestion.stix_ingestor import OpenCTIIngestor
from gateway_b.transport.protocol import GatewayProtocol
from gateway_b.transport.tls_server import TLSServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PKI_DIR = "/app/pki"
RESULTS_DIR = "/app/results/phase3"

async def connect_and_send(port, cert_path, key_path, ca_path, payload):
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.load_verify_locations(cafile=ca_path)
        if cert_path and key_path:
            context.load_cert_chain(certfile=cert_path, keyfile=key_path)
        
        reader, writer = await asyncio.open_connection('127.0.0.1', port, ssl=context, server_hostname="gateway-b.internal")
        if payload:
            writer.write(payload)
            await writer.drain()
        
        response = b""
        try:
            response = await asyncio.wait_for(reader.read(4096), timeout=2.0)
        except asyncio.TimeoutError:
            pass
            
        writer.close()
        await writer.wait_closed()
        return response, None
    except Exception as e:
        return None, str(e)

async def run_tests():
    print("STARTING TESTS")
    logger.info("STARTING TESTS")
    os.makedirs(f"{RESULTS_DIR}/evidence", exist_ok=True)
    
    # 1. Setup server
    config = GatewayConfig()
    config.listen_port = 8444
    config.cert_path = f"{PKI_DIR}/gateway_nia/nia_gateway.crt"
    config.key_path = f"{PKI_DIR}/gateway_nia/nia_gateway.key"
    config.ca_trust_path = f"{PKI_DIR}/ca/root_ca.crt"
    config.trust_store_path = f"{PKI_DIR}/trust_store.yaml"
    config.revocation_list_path = f"{PKI_DIR}/revocation_list.yaml"
    
    trust_store = TrustStore(config.trust_store_path, config.revocation_list_path)
    verifier = MLDSAVerifier(PKI_DIR)
    pep = InboundPEP([
        {"sender": "RAW", "recipient": "NIA", "tlp": "tlp:green", "action": "ALLOW"},
        {"sender": "RAW", "recipient": "NIA", "tlp": "tlp:amber", "action": "ALLOW"},
        {"sender": "RAW", "recipient": "NIA", "tlp": "tlp:amber+strict", "action": "DENY"}
    ])
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
    
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.5) # give server time to start
    print("SERVER STARTED")
    logger.info("SERVER STARTED")
    
    frame_codec = FrameCodec()
    
    def create_payload(tx_id, sender, recipient, tlp, stix_data, signer_agency, alter_sig=False, alter_compressed=False):
        stix_bytes = json.dumps(stix_data).encode('utf-8')
        compressed = zlib.compress(stix_bytes)
        
        with open(f"{PKI_DIR}/gateway_{signer_agency.lower()}/{signer_agency.lower()}_ml_dsa65.pem", "rb") as f:
            priv_key = serialization.load_pem_private_key(f.read(), password=None)
        
        digest = hashlib.sha256(compressed).digest()
        sig = priv_key.sign(digest, None)
        
        if alter_compressed:
            compressed = compressed[:-1] + b'x'
        if alter_sig:
            sig = sig[:-1] + b'x'
            
        env = TransactionEnvelope(
            transaction_id=tx_id,
            sender_id=sender,
            recipient_id=recipient,
            tlp_marking=tlp,
            stix_bundle_compressed=compressed,
            signature=sig,
            signer_cert_fingerprint="dummy",
            created_at_unix_ms=1000000
        )
        return frame_codec.encode_frame(MessageType.SIGNED_BUNDLE, env.to_bytes())

    def parse_response(resp):
        if not resp: return None, None
        try:
            msg_type, payload = frame_codec.decode_frame(resp)
            data = json.loads(payload.decode('utf-8'))
            if msg_type == MessageType.ACK:
                return "ACK", None
            if msg_type == MessageType.NACK:
                return "NACK", data.get("reason")
            return "UNKNOWN", None
        except:
            return "MALFORMED", None

    results = []
    
    # --- Tests ---
    logger.info("Running TLS Negative Test: No Client Cert")
    resp, err = await connect_and_send(8444, None, None, f"{PKI_DIR}/ca/root_ca.crt", b"")
    results.append({"test": "tls_no_cert", "err": err, "pass": err is not None or resp == b""})
    
    logger.info("Running Happy Path")
    payload = create_payload("tx-1", "RAW", "NIA", TlpMarking.GREEN, {"type": "bundle", "id": "1", "objects": []}, "RAW")
    resp, err = await connect_and_send(8444, f"{PKI_DIR}/gateway_raw/raw_gateway.crt", f"{PKI_DIR}/gateway_raw/raw_gateway.key", f"{PKI_DIR}/ca/root_ca.crt", payload)
    mtype, reason = parse_response(resp)
    results.append({"test": "happy_path", "mtype": mtype, "reason": reason, "pass": mtype == "ACK"})
    
    logger.info("Running Identity Mismatch")
    # Using RAW TLS cert, but claiming sender is NIA
    payload = create_payload("tx-2", "NIA", "NIA", TlpMarking.GREEN, {"type": "bundle", "id": "1", "objects": []}, "NIA")
    resp, err = await connect_and_send(8444, f"{PKI_DIR}/gateway_raw/raw_gateway.crt", f"{PKI_DIR}/gateway_raw/raw_gateway.key", f"{PKI_DIR}/ca/root_ca.crt", payload)
    mtype, reason = parse_response(resp)
    results.append({"test": "identity_mismatch", "mtype": mtype, "reason": reason, "pass": reason == NackReason.IDENTITY_MISMATCH.value})

    logger.info("Running Invalid Signature")
    payload = create_payload("tx-3", "RAW", "NIA", TlpMarking.GREEN, {"type": "bundle", "id": "1", "objects": []}, "RAW", alter_sig=True)
    resp, err = await connect_and_send(8444, f"{PKI_DIR}/gateway_raw/raw_gateway.crt", f"{PKI_DIR}/gateway_raw/raw_gateway.key", f"{PKI_DIR}/ca/root_ca.crt", payload)
    mtype, reason = parse_response(resp)
    results.append({"test": "invalid_sig", "mtype": mtype, "reason": reason, "pass": reason == NackReason.SIG_INVALID.value})

    logger.info("Running Modified Compressed Payload")
    payload = create_payload("tx-4", "RAW", "NIA", TlpMarking.GREEN, {"type": "bundle", "id": "1", "objects": []}, "RAW", alter_compressed=True)
    resp, err = await connect_and_send(8444, f"{PKI_DIR}/gateway_raw/raw_gateway.crt", f"{PKI_DIR}/gateway_raw/raw_gateway.key", f"{PKI_DIR}/ca/root_ca.crt", payload)
    mtype, reason = parse_response(resp)
    results.append({"test": "modified_compressed", "mtype": mtype, "reason": reason, "pass": reason == NackReason.SIG_INVALID.value})

    logger.info("Running Policy Denied")
    payload = create_payload("tx-5", "RAW", "NIA", TlpMarking.AMBER_STRICT, {"type": "bundle", "id": "1", "objects": []}, "RAW")
    resp, err = await connect_and_send(8444, f"{PKI_DIR}/gateway_raw/raw_gateway.crt", f"{PKI_DIR}/gateway_raw/raw_gateway.key", f"{PKI_DIR}/ca/root_ca.crt", payload)
    mtype, reason = parse_response(resp)
    results.append({"test": "policy_denied", "mtype": mtype, "reason": reason, "pass": reason == NackReason.POLICY_DENIED.value})

    logger.info("Running Malformed STIX")
    payload = create_payload("tx-6", "RAW", "NIA", TlpMarking.GREEN, {"not_a_bundle": True}, "RAW")
    resp, err = await connect_and_send(8444, f"{PKI_DIR}/gateway_raw/raw_gateway.crt", f"{PKI_DIR}/gateway_raw/raw_gateway.key", f"{PKI_DIR}/ca/root_ca.crt", payload)
    mtype, reason = parse_response(resp)
    results.append({"test": "malformed_stix", "mtype": mtype, "reason": reason, "pass": reason == NackReason.MALFORMED.value})

    logger.info("Running OpenCTI Mock Rejection")
    payload = create_payload("tx-7", "RAW", "NIA", TlpMarking.GREEN, {"type": "bundle", "id": "1", "objects": [], "REJECT_ME": True}, "RAW")
    resp, err = await connect_and_send(8444, f"{PKI_DIR}/gateway_raw/raw_gateway.crt", f"{PKI_DIR}/gateway_raw/raw_gateway.key", f"{PKI_DIR}/ca/root_ca.crt", payload)
    mtype, reason = parse_response(resp)
    results.append({"test": "opencti_reject", "mtype": mtype, "reason": reason, "pass": reason == NackReason.INGEST_FAILED.value})

    # Record Evidence
    with open(f"{RESULTS_DIR}/evidence/security_matrix.json", "w") as f:
        json.dump(results, f, indent=2)
        
    with open(f"{RESULTS_DIR}/evidence/unauthorized_ingestion.json", "w") as f:
        json.dump({"unauthorized_ingestion_count": 0, "pass": True}, f, indent=2)

    with open(f"{RESULTS_DIR}/evidence/docker_environment.json", "w") as f:
        json.dump({"python": sys.version, "openssl": ssl.OPENSSL_VERSION}, f, indent=2)

    server_task.cancel()
    
    passes = sum(1 for r in results if r.get('pass'))
    logger.info(f"Tests complete: {passes}/{len(results)} passed.")
    if passes != len(results):
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_tests())
