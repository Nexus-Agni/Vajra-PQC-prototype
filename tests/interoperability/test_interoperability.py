import pytest
import uuid
import time
from qstie_common.models.envelope import TransactionEnvelope
from qstie_common.enums.protocol_enums import MessageType, TlpMarking
from qstie_common.protocol.frame_codec import FrameCodec

# We will simulate Gateway A and Gateway B using isolated adapters around the shared contract.
class GatewayAAdapter:
    def __init__(self):
        self.codec = FrameCodec()

    def encode(self, env: TransactionEnvelope) -> bytes:
        return self.codec.encode_frame(MessageType.SIGNED_BUNDLE, env.to_bytes())
        
    def decode(self, data: bytes) -> TransactionEnvelope:
        msg_type, payload = self.codec.decode_frame(data)
        assert msg_type == MessageType.SIGNED_BUNDLE
        return TransactionEnvelope.from_bytes(payload)

class GatewayBAdapter:
    def __init__(self):
        self.codec = FrameCodec()

    def encode(self, env: TransactionEnvelope) -> bytes:
        return self.codec.encode_frame(MessageType.SIGNED_BUNDLE, env.to_bytes())
        
    def decode(self, data: bytes) -> TransactionEnvelope:
        msg_type, payload = self.codec.decode_frame(data)
        assert msg_type == MessageType.SIGNED_BUNDLE
        return TransactionEnvelope.from_bytes(payload)

def test_gateway_a_to_b():
    env = TransactionEnvelope(
        transaction_id=str(uuid.uuid4()),
        sender_id="GatewayA",
        recipient_id="GatewayB",
        tlp_marking=TlpMarking.AMBER,
        stix_bundle_compressed=b"data",
        signature=b"sig",
        signer_cert_fingerprint="fp",
        created_at_unix_ms=int(time.time()*1000)
    )
    
    gw_a = GatewayAAdapter()
    gw_b = GatewayBAdapter()
    
    wire_data = gw_a.encode(env)
    decoded_env = gw_b.decode(wire_data)
    
    assert decoded_env == env

def test_gateway_b_to_a():
    env = TransactionEnvelope(
        transaction_id=str(uuid.uuid4()),
        sender_id="GatewayB",
        recipient_id="GatewayA",
        tlp_marking=TlpMarking.GREEN,
        stix_bundle_compressed=b"data2",
        signature=b"sig2",
        signer_cert_fingerprint="fp2",
        created_at_unix_ms=int(time.time()*1000)
    )
    
    gw_a = GatewayAAdapter()
    gw_b = GatewayBAdapter()
    
    wire_data = gw_b.encode(env)
    decoded_env = gw_a.decode(wire_data)
    
    assert decoded_env == env
