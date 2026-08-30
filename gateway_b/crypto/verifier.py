import hashlib
import logging
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

logger = logging.getLogger(__name__)

class MLDSAVerifier:
    def __init__(self, pki_base_dir: str):
        self.pki_base_dir = pki_base_dir
        self.public_keys = {}  # Cache public keys by path
        
    def _load_public_key(self, pubkey_path: str):
        if pubkey_path in self.public_keys:
            return self.public_keys[pubkey_path]
            
        full_path = f"{self.pki_base_dir}/{pubkey_path}"
        with open(full_path, "rb") as f:
            pubkey = serialization.load_pem_public_key(f.read())
        self.public_keys[pubkey_path] = pubkey
        return pubkey

    def verify_signature(self, compressed_payload: bytes, signature: bytes, pubkey_path: str) -> bool:
        try:
            digest = hashlib.sha256(compressed_payload).digest()
            pubkey = self._load_public_key(pubkey_path)
            
            if isinstance(pubkey, ec.EllipticCurvePublicKey):
                from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
                pubkey.verify(signature, digest, ec.ECDSA(Prehashed(hashes.SHA256())))
            else:
                pubkey.verify(signature, digest, None)
            return True
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
