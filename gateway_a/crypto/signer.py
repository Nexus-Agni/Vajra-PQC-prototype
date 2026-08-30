import hashlib
import logging
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

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
            logger.info(f"Loaded private key from {self.private_key_path}")
        except Exception as e:
            logger.error(f"Failed to load private key: {e}")
            raise

    def sign(self, payload: bytes) -> bytes:
        if not self._private_key:
            raise RuntimeError("Private key not loaded")
            
        digest = hashlib.sha256(payload).digest()
        
        if isinstance(self._private_key, ec.EllipticCurvePrivateKey):
            # Pass the raw payload because ECDSA will hash it, OR pass Prehashed
            # Since gateway_b computes sha256 manually, we must use Prehashed
            from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
            return self._private_key.sign(digest, ec.ECDSA(Prehashed(hashes.SHA256())))
        else:
            return self._private_key.sign(digest, None)
