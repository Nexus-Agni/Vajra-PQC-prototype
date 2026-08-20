import struct
from typing import Tuple, Optional
from qstie_common.enums.protocol_enums import MessageType
from qstie_common.errors.protocol_errors import (
    OversizedFrameError,
    MalformedFrameError,
    InvalidMessageTypeError,
    InvalidPayloadLengthError,
)

# 1 byte msg_type + 4 bytes length
HEADER_FORMAT = ">BI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
DEFAULT_MAX_PAYLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

class FrameCodec:
    def __init__(self, max_payload_size: int = DEFAULT_MAX_PAYLOAD_SIZE):
        self.max_payload_size = max_payload_size

    def encode_frame(self, msg_type: MessageType, payload: bytes) -> bytes:
        if len(payload) > self.max_payload_size:
            raise OversizedFrameError(f"Payload size {len(payload)} exceeds maximum {self.max_payload_size}")
        
        header = struct.pack(HEADER_FORMAT, msg_type.value, len(payload))
        return header + payload

    def decode_frame_stream(self, buffer: bytes) -> Tuple[Optional[MessageType], Optional[bytes], bytes]:
        """
        Attempts to decode a frame from the buffer.
        Returns (msg_type, payload, remaining_buffer).
        If the buffer doesn't have a complete frame yet, returns (None, None, buffer).
        """
        if len(buffer) < HEADER_SIZE:
            return None, None, buffer
            
        msg_type_val, payload_len = struct.unpack(HEADER_FORMAT, buffer[:HEADER_SIZE])
        
        try:
            msg_type = MessageType(msg_type_val)
        except ValueError:
            raise InvalidMessageTypeError(f"Unknown message type: {msg_type_val}")
            
        if payload_len > self.max_payload_size:
            raise OversizedFrameError(f"Declared payload length {payload_len} exceeds maximum {self.max_payload_size}")
            
        total_frame_size = HEADER_SIZE + payload_len
        if len(buffer) < total_frame_size:
            return None, None, buffer
            
        payload = buffer[HEADER_SIZE:total_frame_size]
        remaining = buffer[total_frame_size:]
        
        return msg_type, payload, remaining

    def decode_frame(self, data: bytes) -> Tuple[MessageType, bytes]:
        """
        Decodes a single, complete frame from exactly the provided bytes.
        """
        msg_type, payload, remaining = self.decode_frame_stream(data)
        if msg_type is None or payload is None:
            raise MalformedFrameError("Incomplete frame data.")
        if len(remaining) > 0:
            raise MalformedFrameError("Trailing data after frame.")
        return msg_type, payload
