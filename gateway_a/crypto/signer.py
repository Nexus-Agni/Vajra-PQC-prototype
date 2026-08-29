import hashlib
import logging
import zlib
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)

class MlDsaSigner:
    def __init__(self, private_key_path: str):
        self.private_key_path = private_key_path
        self._private_key = None
        self._load_key()

    def _load_key(self):
        try:
            with open(self.private_key_path, "rb") as f:
                self._private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
            logger.info(f"Loaded ML-DSA-65 private key from {self.private_key_path}")
        except Exception as e:
            logger.error(f"Failed to load ML-DSA-65 private key: {e}")
            raise

    def sign(self, payload: bytes) -> bytes:
        if not self._private_key:
            raise RuntimeError("Private key not loaded")
            
        # The protocol specifies: SHA-256(compressed_wire_payload) -> ML-DSA-65 sign
        digest = hashlib.sha256(payload).digest()
        
        # cryptography's MLDSA verify takes the message directly if Prehashed is used, or the raw message. 
        # Wait, the verifier in Gateway B does:
        # digest = hashlib.sha256(compressed_payload).digest()
        # pubkey.verify(signature, digest, None)
        # Therefore, we MUST pass the digest as the 'message' to sign.
        signature = self._private_key.sign(digest, None)
        return signature
