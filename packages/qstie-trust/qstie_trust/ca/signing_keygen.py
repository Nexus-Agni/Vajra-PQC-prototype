from cryptography.hazmat.primitives.asymmetric import mldsa

def generate_ml_dsa_keypair():
    private_key = mldsa.MLDSA65PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key
