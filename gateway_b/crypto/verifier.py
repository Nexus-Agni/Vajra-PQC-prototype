import hashlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA65PublicKey

class MLDSAVerifier:
    def __init__(self, pki_base_dir: str):
        self.pki_base_dir = pki_base_dir
        self.public_keys = {}  # Cache public keys by path
        
    def _load_public_key(self, pubkey_path: str) -> MLDSA65PublicKey:
        if pubkey_path in self.public_keys:
            return self.public_keys[pubkey_path]
            
        full_path = f"{self.pki_base_dir}/{pubkey_path}"
        with open(full_path, "rb") as f:
            pubkey = serialization.load_pem_public_key(f.read())
        self.public_keys[pubkey_path] = pubkey
        return pubkey

    def verify_signature(self, compressed_payload: bytes, signature: bytes, pubkey_path: str) -> bool:
        """
        Verifies ML-DSA-65 signature.
        Order:
        compressed_payload -> SHA-256 -> verification
        """
        try:
            # 1. SHA-256 of compressed payload
            digest = hashlib.sha256(compressed_payload).digest()
            
            # 2. ML-DSA verification
            pubkey = self._load_public_key(pubkey_path)
            pubkey.verify(signature, digest, None)
            return True
        except Exception:
            return False
