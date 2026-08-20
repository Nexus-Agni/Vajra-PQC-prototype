import pytest
import struct
import random
from qstie_common.protocol.frame_codec import FrameCodec, HEADER_SIZE
from qstie_common.enums.protocol_enums import MessageType
from qstie_common.errors.protocol_errors import (
    OversizedFrameError,
    MalformedFrameError,
    InvalidMessageTypeError,
)

def test_single_round_trip():
    codec = FrameCodec()
    payload = b"hello_world"
    encoded = codec.encode_frame(MessageType.SIGNED_BUNDLE, payload)
    
    msg_type, decoded_payload = codec.decode_frame(encoded)
    assert msg_type == MessageType.SIGNED_BUNDLE
    assert decoded_payload == payload

def test_multiple_consecutive():
    codec = FrameCodec()
    payload1 = b"payload1"
    payload2 = b"payload2"
    
    encoded1 = codec.encode_frame(MessageType.SIGNED_BUNDLE, payload1)
    encoded2 = codec.encode_frame(MessageType.ACK, payload2)
    
    buffer = encoded1 + encoded2
    
    msg_type1, dec_payload1, rem1 = codec.decode_frame_stream(buffer)
    assert msg_type1 == MessageType.SIGNED_BUNDLE
    assert dec_payload1 == payload1
    
    msg_type2, dec_payload2, rem2 = codec.decode_frame_stream(rem1)
    assert msg_type2 == MessageType.ACK
    assert dec_payload2 == payload2
    assert len(rem2) == 0

def test_partial_header():
    codec = FrameCodec()
    encoded = codec.encode_frame(MessageType.ACK, b"payload")
    
    for i in range(1, HEADER_SIZE):
        msg_type, payload, rem = codec.decode_frame_stream(encoded[:i])
        assert msg_type is None
        assert payload is None
        assert rem == encoded[:i]

def test_partial_payload():
    codec = FrameCodec()
    encoded = codec.encode_frame(MessageType.ACK, b"payload")
    
    # Send header + partial payload
    partial_len = HEADER_SIZE + 3
    msg_type, payload, rem = codec.decode_frame_stream(encoded[:partial_len])
    assert msg_type is None
    assert payload is None
    assert rem == encoded[:partial_len]

def test_oversized_frame():
    codec = FrameCodec(max_payload_size=1024)
    with pytest.raises(OversizedFrameError):
        codec.encode_frame(MessageType.ACK, b"A" * 2000)
        
    fake_header = struct.pack(">BI", MessageType.ACK.value, 2000)
    with pytest.raises(OversizedFrameError):
        codec.decode_frame_stream(fake_header + b"A" * 2000)

def test_invalid_msg_type():
    codec = FrameCodec()
    fake_header = struct.pack(">BI", 99, 10)
    with pytest.raises(InvalidMessageTypeError):
        codec.decode_frame_stream(fake_header + b"A" * 10)

def test_zero_length_payload():
    codec = FrameCodec()
    encoded = codec.encode_frame(MessageType.ACK, b"")
    msg_type, payload = codec.decode_frame(encoded)
    assert msg_type == MessageType.ACK
    assert payload == b""
    
def test_max_valid_payload():
    codec = FrameCodec(max_payload_size=100)
    encoded = codec.encode_frame(MessageType.ACK, b"A" * 100)
    msg_type, payload = codec.decode_frame(encoded)
    assert len(payload) == 100
    
def test_payload_one_byte_above_max():
    codec = FrameCodec(max_payload_size=100)
    with pytest.raises(OversizedFrameError):
        codec.encode_frame(MessageType.ACK, b"A" * 101)

def test_decode_frame_trailing_data():
    codec = FrameCodec()
    encoded = codec.encode_frame(MessageType.ACK, b"payload")
    with pytest.raises(MalformedFrameError):
        codec.decode_frame(encoded + b"trailing")

def test_empty_input():
    codec = FrameCodec()
    msg, payload, rem = codec.decode_frame_stream(b"")
    assert msg is None
    assert rem == b""
