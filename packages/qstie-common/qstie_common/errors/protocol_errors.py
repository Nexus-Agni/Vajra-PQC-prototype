class ProtocolError(Exception):
    """Base class for all QS-TIE protocol errors."""
    pass

class FrameError(ProtocolError):
    """Base class for frame decoding/encoding errors."""
    pass

class OversizedFrameError(FrameError):
    """Raised when the declared payload length exceeds the maximum allowed size."""
    pass

class MalformedFrameError(FrameError):
    """Raised when the frame is malformed (e.g., truncated)."""
    pass

class InvalidMessageTypeError(FrameError):
    """Raised when the message type is unknown or invalid."""
    pass

class InvalidPayloadLengthError(FrameError):
    """Raised when the payload length is invalid."""
    pass

class EnvelopeError(ProtocolError):
    """Raised when the envelope is invalid or cannot be reconstructed."""
    pass
