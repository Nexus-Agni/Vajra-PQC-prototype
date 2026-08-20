import pytest
import random
from qstie_common.protocol.frame_codec import FrameCodec
from qstie_common.enums.protocol_enums import MessageType

def test_random_fragmentation():
    # Deterministic seed for reproducibility
    random.seed(42)
    codec = FrameCodec()
    
    # Generate multiple valid frames
    frames = []
    expected_payloads = []
    for i in range(50):
        payload = bytes([random.randint(0, 255) for _ in range(random.randint(10, 500))])
        expected_payloads.append(payload)
        frames.append(codec.encode_frame(MessageType.SIGNED_BUNDLE, payload))
        
    combined_stream = b"".join(frames)
    
    # Randomly fragment the combined stream
    fragments = []
    idx = 0
    while idx < len(combined_stream):
        chunk_size = random.randint(1, 20)
        fragments.append(combined_stream[idx:idx+chunk_size])
        idx += chunk_size
        
    # Reassemble and decode
    decoded_payloads = []
    buffer = b""
    
    for frag in fragments:
        buffer += frag
        while True:
            msg_type, payload, remaining = codec.decode_frame_stream(buffer)
            if msg_type is None:
                break
            assert msg_type == MessageType.SIGNED_BUNDLE
            decoded_payloads.append(payload)
            buffer = remaining
            
    assert len(buffer) == 0
    assert decoded_payloads == expected_payloads
