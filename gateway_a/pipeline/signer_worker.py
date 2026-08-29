import asyncio
import logging
import zlib
import hashlib
from cryptography.x509 import load_pem_x509_certificate

from gateway_a.crypto.signer import MlDsaSigner
from gateway_a.models import GatewayATransaction, TransactionState

logger = logging.getLogger(__name__)

class SignerWorker:
    def __init__(self, in_queue: asyncio.Queue, out_queue: asyncio.Queue, signer: MlDsaSigner, cert_path: str):
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.signer = signer
        self.cert_path = cert_path
        self.running = False
        self.cert_fingerprint = self._load_cert_fingerprint()

    def _load_cert_fingerprint(self) -> str:
        try:
            with open(self.cert_path, "rb") as f:
                cert = load_pem_x509_certificate(f.read())
                # Gateway B verifies using SHA-256 fingerprint
                from cryptography.hazmat.primitives import hashes
                return cert.fingerprint(hashes.SHA256()).hex()
        except Exception as e:
            logger.error(f"Failed to load certificate fingerprint: {e}")
            # fallback to a string for testing if missing
            return "mock_fingerprint"

    async def start(self):
        self.running = True
        while self.running:
            try:
                transaction: GatewayATransaction = await self.in_queue.get()
                
                # 1. Compress
                raw_json = transaction.stix_bundle.raw_json
                compressed_payload = zlib.compress(raw_json)
                
                # We store compressed_payload in the transaction or bundle so we can send it.
                # TransactionEnvelope has stix_bundle_compressed
                # So we attach it to the transaction or create it on the fly. Let's attach to transaction.
                transaction.stix_bundle_compressed = compressed_payload
                
                # 2. Sign
                signature = self.signer.sign(compressed_payload)
                transaction.signature = signature
                transaction.signer_cert_fingerprint = self.cert_fingerprint
                transaction.state = TransactionState.SIGNED
                
                await self.out_queue.put(transaction)
                logger.debug(f"Successfully compressed and signed transaction {transaction.transaction_id}")
                
                self.in_queue.task_done()
                
            except asyncio.CancelledError:
                self.running = False
                break
            except Exception as e:
                logger.error(f"Unexpected error in SignerWorker: {e}")
                self.in_queue.task_done()

    def stop(self):
        self.running = False
