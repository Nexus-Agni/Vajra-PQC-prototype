import pytest
import json
import base64
from pathlib import Path
from qstie_common.models.envelope import TransactionEnvelope
from qstie_common.enums.protocol_enums import MessageType, TlpMarking
from qstie_common.protocol.frame_codec import FrameCodec
from qstie_common.fingerprints.utils import calculate_fingerprint

def test_golden_vectors():
    codec = FrameCodec()
    
    # 1: Normal envelope
    env_normal = TransactionEnvelope(
        transaction_id="tx-normal",
        sender_id="AgencyA",
        recipient_id="AgencyB",
        tlp_marking=TlpMarking.GREEN,
        stix_bundle_compressed=b"normal_data",
        signature=b"sig1",
        signer_cert_fingerprint=calculate_fingerprint(b"cert1"),
        created_at_unix_ms=1700000000000
    )
    
    # 2: Unicode envelope
    env_unicode = TransactionEnvelope(
        transaction_id="tx-unicode",
        sender_id="Ünîcødé",
        recipient_id="Récipiént",
        tlp_marking=TlpMarking.AMBER,
        stix_bundle_compressed=b"data",
        signature=b"sig2",
        signer_cert_fingerprint="fp2",
        created_at_unix_ms=1700000000000
    )
    
    vectors = [
        {"name": "normal", "env": env_normal},
        {"name": "unicode", "env": env_unicode},
    ]
    
    results = []
    
    for v in vectors:
        env = v["env"]
        pb_bytes = env.to_bytes()
        frame_bytes = codec.encode_frame(MessageType.SIGNED_BUNDLE, pb_bytes)
        
        # Verify decoding
        msg_type, decoded_pb = codec.decode_frame(frame_bytes)
        assert msg_type == MessageType.SIGNED_BUNDLE
        decoded_env = TransactionEnvelope.from_bytes(decoded_pb)
        assert decoded_env == env
        
        results.append({
            "name": v["name"],
            "transaction_id": env.transaction_id,
            "pb_size": len(pb_bytes),
            "frame_size": len(frame_bytes),
            "frame_hex_prefix": frame_bytes[:10].hex()
        })
        
    out_dir = Path("results/phase1/evidence")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "golden_vectors.json", "w") as f:
        json.dump(results, f, indent=2)

def test_serialized_size_evidence():
    # Will record serialized sizes for representative envelopes
    # 1. empty/minimal; 2. normal; 3. unicode; 4. binary signature; 5. large payload.
    codec = FrameCodec()
    
    envs = {
        "empty": TransactionEnvelope("", "", "", TlpMarking.GREEN, b"", b"", "", 0),
        "normal": TransactionEnvelope("tx-1", "S1", "R1", TlpMarking.GREEN, b"stix_data_here", b"sig_bytes_here", "fp_here", 1700000000000),
        "unicode": TransactionEnvelope("tx-2", "Ünîcødé", "🚀", TlpMarking.AMBER, b"data", b"sig", "fp", 1700000000000),
        "binary_signature": TransactionEnvelope("tx-3", "S1", "R1", TlpMarking.GREEN, b"data", bytes([x % 256 for x in range(2000)]), "fp", 1700000000000),
        "large_payload": TransactionEnvelope("tx-4", "S1", "R1", TlpMarking.GREEN, b"A"*1000000, b"sig", "fp", 1700000000000),
    }
    
    evidence = []
    for name, env in envs.items():
        pb_bytes = env.to_bytes()
        frame_bytes = codec.encode_frame(MessageType.SIGNED_BUNDLE, pb_bytes)
        evidence.append({
            "scenario": name,
            "protobuf_payload_size_bytes": len(pb_bytes),
            "complete_frame_size_bytes": len(frame_bytes)
        })
        
    out_dir = Path("results/phase1/evidence")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "size_evidence.json", "w") as f:
        json.dump(evidence, f, indent=2)
