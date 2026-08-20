import pytest
import struct
from qstie_common.protocol.frame_codec import FrameCodec
from qstie_common.enums.protocol_enums import MessageType

def test_independent_wire_inspection():
    codec = FrameCodec()
    payload = b"test_payload_12345"
    msg_type = MessageType.SIGNED_BUNDLE
    
    wire_bytes = codec.encode_frame(msg_type, payload)
    
    # Independent inspection
    assert wire_bytes[0] == msg_type.value
    reported_length = struct.unpack(">I", wire_bytes[1:5])[0]
    assert reported_length == len(payload)
    
    actual_payload = wire_bytes[5:]
    assert actual_payload == payload
    assert len(actual_payload) == reported_length
