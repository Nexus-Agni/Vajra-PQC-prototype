import asyncio
import json
import logging
import pytest
import zlib
import hashlib
import os
from datetime import datetime
import sys
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import mldsa

from gateway_a.crypto.signer import MlDsaSigner
from gateway_a.pipeline.signer_worker import SignerWorker
from gateway_a.models import GatewayATransaction, StixBundle
from qstie_common.enums.protocol_enums import TlpMarking

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@pytest.fixture
def keys(tmp_path):
    private_key = mldsa.MLDSA65PrivateKey.generate()
    public_key = private_key.public_key()
    
    priv_path = tmp_path / "priv.pem"
    pub_path = tmp_path / "pub.pem"
    
    with open(priv_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
        
    with open(pub_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
        
    wrong_private_key = mldsa.MLDSA65PrivateKey.generate()
    wrong_public_key = wrong_private_key.public_key()
    wrong_pub_path = tmp_path / "wrong_pub.pem"
    with open(wrong_pub_path, "wb") as f:
        f.write(wrong_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
        
    cert_path = tmp_path / "dummy.crt"
    with open(cert_path, "wb") as f:
        f.write(b"mock cert content") # We just need the file to exist, the load_cert_fingerprint handles failures

    return {
        "priv_path": str(priv_path),
        "pub_path": str(pub_path),
        "wrong_pub_path": str(wrong_pub_path),
        "cert_path": str(cert_path),
        "pub_key_obj": public_key,
        "wrong_pub_key_obj": wrong_public_key
    }


@pytest.mark.asyncio
async def test_compression_and_signing(keys):
    in_queue = asyncio.Queue()
    out_queue = asyncio.Queue()
    
    signer = MlDsaSigner(keys["priv_path"])
    worker = SignerWorker(in_queue, out_queue, signer, keys["cert_path"])
    
    task = asyncio.create_task(worker.start())
    
    # Generate some dummy JSON representing a STIX bundle
    dummy_stix = {
        "type": "bundle",
        "id": "bundle--123",
        "objects": [{"type": "indicator", "id": "indicator--456", "name": "Test " * 50}] # Repeats for good compression
    }
    raw_json = json.dumps(dummy_stix).encode('utf-8')
    raw_len = len(raw_json)
    
    bundle = StixBundle(
        bundle_id="bundle--123",
        raw_json=raw_json,
        tlp_marking=TlpMarking.AMBER,
        misp_event_uuid="1234"
    )
    
    tx = GatewayATransaction(stix_bundle=bundle)
    await in_queue.put(tx)
    
    try:
        processed_tx = await asyncio.wait_for(out_queue.get(), timeout=2.0)
    except asyncio.TimeoutError:
        pytest.fail("Worker did not process transaction")
        
    worker.stop()
    task.cancel()
    
    comp_evidence = []
    sign_evidence = []
    
    # === COMPRESSION TESTS ===
    compressed_payload = processed_tx.stix_bundle_compressed
    comp_len = len(compressed_payload)
    comp_ratio = raw_len / comp_len if comp_len > 0 else 0
    
    assert comp_len < raw_len, "Compression did not reduce size"
    # Ensure it decompresses back to original
    assert zlib.decompress(compressed_payload) == raw_json
    
    comp_evidence.append({
        "test": "compression characteristics",
        "status": "PASS",
        "details": f"raw_payload_size: {raw_len}, compressed_payload_size: {comp_len}, compression_ratio: {comp_ratio:.2f}"
    })
    
    # === SIGNING TESTS ===
    signature = processed_tx.signature
    
    def verify(pub_key, payload, sig):
        try:
            digest = hashlib.sha256(payload).digest()
            pub_key.verify(sig, digest, None)
            return True
        except Exception:
            return False

    # 1. verify with correct public key
    assert verify(keys["pub_key_obj"], compressed_payload, signature)
    sign_evidence.append({
        "test": "sign valid payload and verify with correct public key",
        "status": "PASS"
    })
    
    # 2. sign same payload repeatedly
    sig2 = signer.sign(compressed_payload)
    sig3 = signer.sign(compressed_payload)
    assert verify(keys["pub_key_obj"], compressed_payload, sig2)
    assert verify(keys["pub_key_obj"], compressed_payload, sig3)
    sign_evidence.append({
        "test": "sign same payload repeatedly",
        "status": "PASS"
    })
    
    # 3. modify payload
    modified_payload = compressed_payload + b"x"
    assert not verify(keys["pub_key_obj"], modified_payload, signature)
    sign_evidence.append({
        "test": "modify payload -> verification fails",
        "status": "PASS"
    })
    
    # 4. modify signature
    modified_signature = signature[:-1] + (b"x" if signature[-1:] != b"x" else b"y")
    assert not verify(keys["pub_key_obj"], compressed_payload, modified_signature)
    sign_evidence.append({
        "test": "modify signature -> verification fails",
        "status": "PASS"
    })
    
    # 5. wrong public key
    assert not verify(keys["wrong_pub_key_obj"], compressed_payload, signature)
    sign_evidence.append({
        "test": "verify with wrong public key -> verification fails",
        "status": "PASS"
    })
    
    os.makedirs("results/phase4/evidence", exist_ok=True)
    
    with open("results/phase4/evidence/compression_validation.json", "w") as f:
        json.dump({"timestamp": datetime.utcnow().isoformat(), "environment": "mock", "results": comp_evidence}, f, indent=2)
        
    with open("results/phase4/evidence/signing_validation.json", "w") as f:
        json.dump({"timestamp": datetime.utcnow().isoformat(), "environment": "mock", "results": sign_evidence}, f, indent=2)

