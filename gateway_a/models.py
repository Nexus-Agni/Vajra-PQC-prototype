from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from qstie_common.enums.protocol_enums import TlpMarking

class TransactionState(str, Enum):
    RECEIVED = "received"
    VALIDATED = "validated"
    SIGNED = "signed"
    POLICY_APPROVED = "policy_approved"
    POLICY_REJECTED = "policy_rejected"
    SENDING = "sending"
    ACKED = "acked"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"

@dataclass
class StixBundle:
    bundle_id: str
    raw_json: bytes
    tlp_marking: TlpMarking
    misp_event_uuid: str

@dataclass
class GatewayATransaction:
    transaction_id: UUID = field(default_factory=uuid4)
    sender_id: str = "RAW"
    recipient_id: str = "NIA"
    stix_bundle: Optional[StixBundle] = None
    signature: bytes = b""
    signer_cert_fingerprint: str = ""
    state: TransactionState = TransactionState.RECEIVED
    created_at: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
