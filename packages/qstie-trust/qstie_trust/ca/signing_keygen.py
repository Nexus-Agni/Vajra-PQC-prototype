from cryptography.hazmat.primitives.asymmetric import mldsa, ec
from cryptography.hazmat.primitives import hashes

def generate_ml_dsa_keypair() -> tuple[object, object]:
    private_key = mldsa.MLDSA65PrivateKey.generate()
    return private_key, private_key.public_key()

def generate_ecdsa_keypair() -> tuple[object, object]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key, private_key.public_key()
