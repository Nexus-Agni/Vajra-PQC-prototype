import pytest
import struct
from qstie_common.protocol.frame_codec import FrameCodec, HEADER_SIZE
from qstie_common.enums.protocol_enums import MessageType
from qstie_common.errors.protocol_errors import (
    OversizedFrameError,
    MalformedFrameError,
    InvalidMessageTypeError,
    EnvelopeError,
)
from qstie_common.models.envelope import TransactionEnvelope

# Security matrix test cases

def test_zero_length():
    codec = FrameCodec()
    encoded = codec.encode_frame(MessageType.SIGNED_BUNDLE, b"")
    msg_type, payload = codec.decode_frame(encoded)
    assert msg_type == MessageType.SIGNED_BUNDLE
    assert payload == b""

def test_uint32_max_declared_length():
    codec = FrameCodec(max_payload_size=1024)
    header = struct.pack(">BI", MessageType.ACK.value, 4294967295)
    with pytest.raises(OversizedFrameError):
        codec.decode_frame_stream(header)

def test_huge_declared_length():
    codec = FrameCodec(max_payload_size=10 * 1024 * 1024)
    # Exceeds max payload size by a lot
    header = struct.pack(">BI", MessageType.ACK.value, 100 * 1024 * 1024)
    with pytest.raises(OversizedFrameError):
        codec.decode_frame_stream(header)

def test_oversized_declared_length():
    codec = FrameCodec(max_payload_size=1024)
    header = struct.pack(">BI", MessageType.ACK.value, 1025)
    with pytest.raises(OversizedFrameError):
        codec.decode_frame_stream(header)

def test_oversized_actual_payload():
    codec = FrameCodec(max_payload_size=1024)
    with pytest.raises(OversizedFrameError):
        codec.encode_frame(MessageType.ACK, b"A" * 1025)

def test_truncated_1_byte_header():
    codec = FrameCodec()
    msg, payload, rem = codec.decode_frame_stream(b"")
    assert msg is None
    assert payload is None
    assert rem == b""

def test_truncated_length_field():
    codec = FrameCodec()
    header = struct.pack(">BI", MessageType.ACK.value, 10)
    msg, payload, rem = codec.decode_frame_stream(header[:3])
    assert msg is None
    assert payload is None
    assert rem == header[:3]

def test_truncated_payload():
    codec = FrameCodec()
    header = struct.pack(">BI", MessageType.ACK.value, 10)
    msg, payload, rem = codec.decode_frame_stream(header + b"A" * 5)
    assert msg is None
    assert payload is None
    assert rem == header + b"A" * 5

def test_malformed_protobuf():
    with pytest.raises(EnvelopeError):
        TransactionEnvelope.from_bytes(b"garbage_data_here123")

def test_garbage_bytes():
    codec = FrameCodec()
    garbage = bytes([255, 255, 255, 255, 255])
    with pytest.raises(InvalidMessageTypeError):
        codec.decode_frame_stream(garbage)

def test_unknown_message_type():
    codec = FrameCodec()
    header = struct.pack(">BI", 255, 10)
    with pytest.raises(InvalidMessageTypeError):
        codec.decode_frame_stream(header + b"A" * 10)

def test_invalid_message_type():
    codec = FrameCodec()
    header = struct.pack(">BI", 0, 10)
    with pytest.raises(InvalidMessageTypeError):
        codec.decode_frame_stream(header + b"A" * 10)

def test_payload_length_mismatch():
    codec = FrameCodec()
    header = struct.pack(">BI", MessageType.ACK.value, 10)
    msg, payload, rem = codec.decode_frame_stream(header + b"A" * 20)
    # The decoder will successfully decode the first 10 bytes and leave 10 bytes as remaining
    assert msg == MessageType.ACK
    assert payload == b"A" * 10
    assert len(rem) == 10

def test_concatenated_malformed_and_valid():
    codec = FrameCodec()
    header_malformed = struct.pack(">BI", 255, 10)
    valid_frame = codec.encode_frame(MessageType.ACK, b"valid")
    buffer = header_malformed + valid_frame
    
    with pytest.raises(InvalidMessageTypeError):
        codec.decode_frame_stream(buffer)

def test_multiple_malicious_frames():
    codec = FrameCodec(max_payload_size=1024)
    header1 = struct.pack(">BI", MessageType.ACK.value, 4294967295)
    header2 = struct.pack(">BI", 255, 10)
    
    with pytest.raises(OversizedFrameError):
        codec.decode_frame_stream(header1 + header2)

# Stream recovery is not supported natively by this basic framing protocol,
# so we do not expect it to automatically resynchronize.
