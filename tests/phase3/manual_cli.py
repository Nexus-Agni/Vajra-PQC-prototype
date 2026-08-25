import asyncio
import sys
import os
import json
import zlib
import hashlib
from cryptography.hazmat.primitives import serialization
from qstie_common.models.envelope import TransactionEnvelope
from qstie_common.enums.protocol_enums import TlpMarking, MessageType, NackReason
from qstie_common.protocol.frame_codec import FrameCodec

# For TLS client
import ssl

async def main():
    scenario = sys.argv[1]
    
    PKI_DIR = "/app/pki"
    frame_codec = FrameCodec()
    
    def create_payload(tx_id, sender, recipient, tlp, stix_data, signer_agency, alter_sig=False, alter_compressed=False, malformed_frame=False, malformed_stix=False):
        if malformed_stix:
            stix_bytes = b"not a json"
        else:
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
        payload = frame_codec.encode_frame(MessageType.SIGNED_BUNDLE, env.to_bytes())
        if malformed_frame:
            payload = payload[:-5]
        return payload

    cert_path = f"{PKI_DIR}/gateway_raw/raw_gateway.crt"
    key_path = f"{PKI_DIR}/gateway_raw/raw_gateway.key"
    ca_path = f"{PKI_DIR}/ca/root_ca.crt"
    payload = None

    if scenario == "no_client_cert":
        cert_path = None
        key_path = None
        payload = b""
    elif scenario == "wrong_cert":
        cert_path = f"{PKI_DIR}/tls_wrong_ca/wrong.crt"
        key_path = f"{PKI_DIR}/tls_wrong_ca/wrong.key"
        payload = b""
    elif scenario == "forged_sender":
        payload = create_payload("tx-man-1", "NIA", "NIA", TlpMarking.GREEN, {"type":"bundle","id":"1","objects":[]}, "NIA")
    elif scenario == "modified_sig":
        payload = create_payload("tx-man-2", "RAW", "NIA", TlpMarking.GREEN, {"type":"bundle","id":"1","objects":[]}, "RAW", alter_sig=True)
    elif scenario == "modified_compressed":
        payload = create_payload("tx-man-3", "RAW", "NIA", TlpMarking.GREEN, {"type":"bundle","id":"1","objects":[]}, "RAW", alter_compressed=True)
    elif scenario == "denied_tlp":
        payload = create_payload("tx-man-4", "RAW", "NIA", TlpMarking.AMBER_STRICT, {"type":"bundle","id":"1","objects":[]}, "RAW")
    elif scenario == "malformed_frame":
        payload = create_payload("tx-man-5", "RAW", "NIA", TlpMarking.GREEN, {"type":"bundle","id":"1","objects":[]}, "RAW", malformed_frame=True)
    elif scenario == "malformed_stix":
        payload = create_payload("tx-man-6", "RAW", "NIA", TlpMarking.GREEN, {"type":"bundle","id":"1","objects":[]}, "RAW", malformed_stix=True)
    else:
        print("Unknown scenario")
        sys.exit(1)

    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.load_verify_locations(cafile=ca_path)
        if cert_path and key_path:
            context.load_cert_chain(certfile=cert_path, keyfile=key_path)
        
        reader, writer = await asyncio.open_connection('127.0.0.1', 8443, ssl=context, server_hostname="gateway-b.internal")
        if payload:
            writer.write(payload)
            await writer.drain()
        
        resp = b""
        try:
            resp = await asyncio.wait_for(reader.read(4096), timeout=2.0)
        except asyncio.TimeoutError:
            pass
        writer.close()
        await writer.wait_closed()
        
        if not resp:
            print(json.dumps({"status": "connection_closed_or_empty"}))
        else:
            msg_type, body = frame_codec.decode_frame(resp)
            decoded_body = json.loads(body.decode('utf-8'))
            print(json.dumps({"status": "received", "msg_type": str(msg_type), "body": decoded_body}))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))

if __name__ == "__main__":
    asyncio.run(main())
