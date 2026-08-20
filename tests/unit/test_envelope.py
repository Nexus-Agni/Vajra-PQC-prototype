import pytest
import time
import uuid
from qstie_common.models.envelope import TransactionEnvelope
from qstie_common.enums.protocol_enums import TlpMarking
from qstie_common.errors.protocol_errors import EnvelopeError
from qstie_common.fingerprints.utils import calculate_fingerprint

def test_empty_envelope():
    env = TransactionEnvelope(
        transaction_id="",
        sender_id="",
        recipient_id="",
        tlp_marking=TlpMarking.GREEN,
        stix_bundle_compressed=b"",
        signature=b"",
        signer_cert_fingerprint="",
        created_at_unix_ms=0,
    )
    serialized = env.to_bytes()
    decoded = TransactionEnvelope.from_bytes(serialized)
    assert decoded.transaction_id == ""
    assert decoded.stix_bundle_compressed == b""

def test_normal_envelope():
    env = TransactionEnvelope(
        transaction_id=str(uuid.uuid4()),
        sender_id="AgencyA",
        recipient_id="AgencyB",
        tlp_marking=TlpMarking.AMBER,
        stix_bundle_compressed=b"compressed_data",
        signature=b"sig",
        signer_cert_fingerprint=calculate_fingerprint(b"cert_data"),
        created_at_unix_ms=int(time.time() * 1000),
    )
    decoded = TransactionEnvelope.from_bytes(env.to_bytes())
    assert decoded == env

def test_unicode_fields():
    env = TransactionEnvelope(
        transaction_id=str(uuid.uuid4()),
        sender_id="Ünîcødé_Agency_🚀",
        recipient_id="Récipiént",
        tlp_marking=TlpMarking.AMBER_STRICT,
        stix_bundle_compressed=b"payload",
        signature=b"sig",
        signer_cert_fingerprint="abc",
        created_at_unix_ms=123,
    )
    decoded = TransactionEnvelope.from_bytes(env.to_bytes())
    assert decoded.sender_id == "Ünîcødé_Agency_🚀"

def test_binary_signature():
    sig = bytes([x % 256 for x in range(1024)])
    env = TransactionEnvelope(
        transaction_id="id",
        sender_id="A",
        recipient_id="B",
        tlp_marking=TlpMarking.GREEN,
        stix_bundle_compressed=b"payload",
        signature=sig,
        signer_cert_fingerprint="abc",
        created_at_unix_ms=123,
    )
    decoded = TransactionEnvelope.from_bytes(env.to_bytes())
    assert decoded.signature == sig

def test_large_envelope():
    large_payload = b"A" * 5 * 1024 * 1024 # 5 MB
    env = TransactionEnvelope(
        transaction_id="id",
        sender_id="A",
        recipient_id="B",
        tlp_marking=TlpMarking.GREEN,
        stix_bundle_compressed=large_payload,
        signature=b"sig",
        signer_cert_fingerprint="abc",
        created_at_unix_ms=123,
    )
    decoded = TransactionEnvelope.from_bytes(env.to_bytes())
    assert len(decoded.stix_bundle_compressed) == len(large_payload)

def test_uuid_timestamp_preservation():
    uid = str(uuid.uuid4())
    ts = 1718000000000
    env = TransactionEnvelope(
        transaction_id=uid,
        sender_id="A",
        recipient_id="B",
        tlp_marking=TlpMarking.GREEN,
        stix_bundle_compressed=b"",
        signature=b"",
        signer_cert_fingerprint="",
        created_at_unix_ms=ts,
    )
    decoded = TransactionEnvelope.from_bytes(env.to_bytes())
    assert decoded.transaction_id == uid
    assert decoded.created_at_unix_ms == ts

def test_fingerprint_preservation():
    fp = calculate_fingerprint(b"cert_data")
    env = TransactionEnvelope(
        transaction_id="id",
        sender_id="A",
        recipient_id="B",
        tlp_marking=TlpMarking.GREEN,
        stix_bundle_compressed=b"",
        signature=b"",
        signer_cert_fingerprint=fp,
        created_at_unix_ms=123,
    )
    decoded = TransactionEnvelope.from_bytes(env.to_bytes())
    assert decoded.signer_cert_fingerprint == fp

def test_malformed_protobuf():
    with pytest.raises(EnvelopeError):
        TransactionEnvelope.from_bytes(b"garbage_data")
