import pytest
import asyncio
import ssl
import zlib
import json
import hashlib
from qstie_common.models.envelope import TransactionEnvelope
from qstie_common.enums.protocol_enums import TlpMarking, MessageType, NackReason
from qstie_common.protocol.frame_codec import FrameCodec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import mldsa
from qstie_common.protocol.qstie_pb2 import NackMessage, AckMessage

@pytest.fixture
def frame_codec():
    return FrameCodec()

async def connect_and_send(port, cert_path, key_path, ca_path, payload):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.load_verify_locations(cafile=ca_path)
    context.load_cert_chain(certfile=cert_path, keyfile=key_path)
    
    reader, writer = await asyncio.open_connection('127.0.0.1', port, ssl=context)
    writer.write(payload)
    await writer.drain()
    
    response = await reader.read(4096)
    writer.close()
    await writer.wait_closed()
    return response

@pytest.mark.asyncio
async def test_happy_path(gateway_server, pki_dir, frame_codec):
    # Setup test envelope
    stix = {"type": "bundle", "id": "bundle--123", "objects": []}
    stix_bytes = json.dumps(stix).encode('utf-8')
    compressed = zlib.compress(stix_bytes)
    
    # Sign it
    with open(f"{pki_dir}/gateway_raw/raw_ml_dsa65.pem", "rb") as f:
        priv_key = serialization.load_pem_private_key(f.read(), password=None)
    
    digest = hashlib.sha256(compressed).digest()
    sig = priv_key.sign(digest, None)
    
    env = TransactionEnvelope(
        transaction_id="tx-123",
        sender_id="RAW",
        recipient_id="NIA",
        tlp_marking=TlpMarking.GREEN,
        stix_bundle_compressed=compressed,
        signature=sig,
        signer_cert_fingerprint="dummy", # Not strictly checked for value in verifier yet, but identity cross-check checks TLS peer cert FP
        created_at_unix_ms=1000000
    )
    
    payload = frame_codec.encode_frame(MessageType.SIGNED_BUNDLE, env.to_bytes())
    
    response = await connect_and_send(
        gateway_server['port'],
        f"{pki_dir}/gateway_raw/raw_gateway.crt",
        f"{pki_dir}/gateway_raw/raw_gateway.key",
        f"{pki_dir}/ca/root_ca.crt",
        payload
    )
    
    assert response != b""
    msg_type, resp_payload = frame_codec.decode_frame(response)
    assert msg_type == MessageType.ACK
    
    ack = AckMessage()
    ack.ParseFromString(resp_payload)
    assert ack.transaction_id == "tx-123"
    assert gateway_server['ingestor'].invocation_count == 1

@pytest.mark.asyncio
async def test_identity_mismatch(gateway_server, pki_dir, frame_codec):
    stix = {"type": "bundle", "id": "bundle--123", "objects": []}
    stix_bytes = json.dumps(stix).encode('utf-8')
    compressed = zlib.compress(stix_bytes)
    with open(f"{pki_dir}/gateway_raw/raw_ml_dsa65.pem", "rb") as f:
        priv_key = serialization.load_pem_private_key(f.read(), password=None)
    digest = hashlib.sha256(compressed).digest()
    sig = priv_key.sign(digest, None)
    env = TransactionEnvelope(
        transaction_id="tx-124",
        sender_id="NIA", # Forged sender! The TLS cert is RAW
        recipient_id="RAW",
        tlp_marking=TlpMarking.GREEN,
        stix_bundle_compressed=compressed,
        signature=sig,
        signer_cert_fingerprint="dummy",
        created_at_unix_ms=1000000
    )
    payload = frame_codec.encode_frame(MessageType.SIGNED_BUNDLE, env.to_bytes())
    response = await connect_and_send(
        gateway_server['port'],
        f"{pki_dir}/gateway_raw/raw_gateway.crt",
        f"{pki_dir}/gateway_raw/raw_gateway.key",
        f"{pki_dir}/ca/root_ca.crt",
        payload
    )
    msg_type, resp_payload = frame_codec.decode_frame(response)
    assert msg_type == MessageType.NACK
    nack = NackMessage()
    nack.ParseFromString(resp_payload)
    assert nack.reason == NackReason.IDENTITY_MISMATCH.value
    assert gateway_server['ingestor'].invocation_count == 1  # From first test


@pytest.mark.asyncio
async def test_invalid_signature(gateway_server, pki_dir, frame_codec):
    stix = {"type": "bundle", "id": "bundle--123", "objects": []}
    compressed = zlib.compress(json.dumps(stix).encode('utf-8'))
    env = TransactionEnvelope(
        transaction_id="tx-invalid-sig",
        sender_id="RAW",
        recipient_id="NIA",
        tlp_marking=TlpMarking.GREEN,
        stix_bundle_compressed=compressed,
        signature=b'bad_signature',
        signer_cert_fingerprint="dummy",
        created_at_unix_ms=1000000
    )
    payload = frame_codec.encode_frame(MessageType.SIGNED_BUNDLE, env.to_bytes())
    response = await connect_and_send(
        gateway_server['port'],
        f"{pki_dir}/gateway_raw/raw_gateway.crt",
        f"{pki_dir}/gateway_raw/raw_gateway.key",
        f"{pki_dir}/ca/root_ca.crt",
        payload
    )
    msg_type, resp_payload = frame_codec.decode_frame(response)
    assert msg_type == MessageType.NACK
    nack = NackMessage()
    nack.ParseFromString(resp_payload)
    assert nack.reason == NackReason.SIG_INVALID.value

