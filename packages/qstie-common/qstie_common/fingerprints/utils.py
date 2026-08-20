import hashlib

def calculate_fingerprint(data: bytes) -> str:
    """
    Calculates a deterministic fingerprint for binary data.
    Uses SHA-256 and returns a canonical lowercase hex string.
    
    The project's defined fingerprint/hash convention uses SHA-256.
    """
    if not isinstance(data, bytes):
        raise TypeError("Fingerprint input must be explicitly bytes.")
    
    digest = hashlib.sha256(data).hexdigest()
    return digest.lower()
