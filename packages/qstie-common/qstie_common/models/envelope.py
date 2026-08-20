from dataclasses import dataclass
from typing import Optional
from qstie_common.protocol.qstie_pb2 import TransactionEnvelope as ProtoTransactionEnvelope
from qstie_common.enums.protocol_enums import TlpMarking
from qstie_common.errors.protocol_errors import EnvelopeError

@dataclass
class TransactionEnvelope:
    transaction_id: str
    sender_id: str
    recipient_id: str
    tlp_marking: TlpMarking
    stix_bundle_compressed: bytes
    signature: bytes
    signer_cert_fingerprint: str
    created_at_unix_ms: int

    @classmethod
    def from_proto(cls, proto_env: ProtoTransactionEnvelope) -> 'TransactionEnvelope':
        try:
            return cls(
                transaction_id=proto_env.transaction_id,
                sender_id=proto_env.sender_id,
                recipient_id=proto_env.recipient_id,
                tlp_marking=TlpMarking(proto_env.tlp_marking) if proto_env.tlp_marking else TlpMarking.GREEN,
                stix_bundle_compressed=proto_env.stix_bundle_compressed,
                signature=proto_env.signature,
                signer_cert_fingerprint=proto_env.signer_cert_fingerprint,
                created_at_unix_ms=proto_env.created_at_unix_ms,
            )
        except ValueError as e:
            raise EnvelopeError(f"Invalid field in envelope: {e}")

    def to_proto(self) -> ProtoTransactionEnvelope:
        env = ProtoTransactionEnvelope()
        env.transaction_id = self.transaction_id
        env.sender_id = self.sender_id
        env.recipient_id = self.recipient_id
        env.tlp_marking = self.tlp_marking.value
        env.stix_bundle_compressed = self.stix_bundle_compressed
        env.signature = self.signature
        env.signer_cert_fingerprint = self.signer_cert_fingerprint
        env.created_at_unix_ms = self.created_at_unix_ms
        return env

    @classmethod
    def from_bytes(cls, data: bytes) -> 'TransactionEnvelope':
        env = ProtoTransactionEnvelope()
        try:
            env.ParseFromString(data)
        except Exception as e:
            raise EnvelopeError(f"Failed to parse protobuf: {e}")
        return cls.from_proto(env)

    def to_bytes(self) -> bytes:
        return self.to_proto().SerializeToString()
