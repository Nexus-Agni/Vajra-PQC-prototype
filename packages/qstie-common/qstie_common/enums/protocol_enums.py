from enum import Enum, IntEnum

class MessageType(IntEnum):
    SIGNED_BUNDLE = 0x01
    ACK = 0x02
    NACK = 0x03

class NackReason(str, Enum):
    SIG_INVALID = "SIG_INVALID"
    POLICY_DENIED = "POLICY_DENIED"
    MALFORMED = "MALFORMED"
    UNKNOWN_SENDER = "UNKNOWN_SENDER"
    INGEST_FAILED = "INGEST_FAILED"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    REVOKED_CERT = "REVOKED_CERT"

class TransactionState(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FAILED = "FAILED"

class TlpMarking(str, Enum):
    GREEN = "tlp:green"
    AMBER = "tlp:amber"
    AMBER_STRICT = "tlp:amber+strict"
