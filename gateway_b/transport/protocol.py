import asyncio
import zlib
import json
import logging
from typing import Optional

from qstie_common.protocol.frame_codec import FrameCodec
from qstie_common.models.envelope import TransactionEnvelope
from qstie_common.enums.protocol_enums import MessageType, NackReason
from qstie_common.errors.protocol_errors import (
    OversizedFrameError, MalformedFrameError, InvalidMessageTypeError
)
from gateway_b.crypto.verifier import MLDSAVerifier
from gateway_b.policy.pep_inbound import InboundPEP
from gateway_b.ingestion.stix_ingestor import OpenCTIIngestor
from gateway_b.trust.cert_store import TrustStore
import traceback

logger = logging.getLogger(__name__)

class GatewayProtocol:
    def __init__(
        self,
        trust_store: TrustStore,
        verifier: MLDSAVerifier,
        pep: InboundPEP,
        ingestor: OpenCTIIngestor
    ):
        self.trust_store = trust_store
        self.verifier = verifier
        self.pep = pep
        self.ingestor = ingestor
        self.frame_codec = FrameCodec()

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer_cert = writer.get_extra_info('peercert')
        # We need the raw DER cert to compute fingerprint.
        # However, asyncio ssl object provides it via get_extra_info('ssl_object').getpeercert(binary_form=True)
        ssl_obj = writer.get_extra_info('ssl_object')
        if ssl_obj:
            der_cert = ssl_obj.getpeercert(binary_form=True)
            import hashlib
            peer_fingerprint = hashlib.sha256(der_cert).hexdigest()
        else:
            peer_fingerprint = "UNKNOWN"

        try:
            # 1. Read frame
            buffer = b""
            while True:
                data = await reader.read(4096)
                logger.info(f"Read {len(data)} bytes")
                if not data:
                    break
                buffer += data
                
                try:
                    msg_type, payload, remaining = self.frame_codec.decode_frame_stream(buffer)
                    logger.info(f"Decode result: {msg_type}")
                    if msg_type is not None:
                        # We have a full frame.
                        if remaining:
                            # Frame followed by extra bytes -> malformed in this context
                            await self.send_nack(writer, "0", NackReason.MALFORMED)
                            return
                            
                        if msg_type != MessageType.SIGNED_BUNDLE:
                            await self.send_nack(writer, "0", NackReason.MALFORMED)
                            return

                        await self.process_transaction(writer, payload, peer_fingerprint)
                        return # Exactly one transaction per connection, then close
                except (OversizedFrameError, MalformedFrameError, InvalidMessageTypeError) as e:
                    logger.error(f"Frame error: {e}")
                    await self.send_nack(writer, "0", NackReason.MALFORMED)
                    return
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def send_nack(self, writer: asyncio.StreamWriter, tx_id: str, reason: NackReason):
        payload = json.dumps({"transaction_id": tx_id, "reason": reason.value}).encode('utf-8')
        frame = self.frame_codec.encode_frame(MessageType.NACK, payload)
        writer.write(frame)
        await writer.drain()

    async def send_ack(self, writer: asyncio.StreamWriter, tx_id: str):
        payload = json.dumps({"transaction_id": tx_id}).encode('utf-8')
        frame = self.frame_codec.encode_frame(MessageType.ACK, payload)
        writer.write(frame)
        await writer.drain()

    async def process_transaction(self, writer: asyncio.StreamWriter, payload: bytes, peer_fingerprint: str):
        tx_id = "0"
        import time
        t_received = time.time_ns()
        t_verified = 0
        t_ingested = 0
        try:
            # 2. Protobuf decode
            try:
                envelope = TransactionEnvelope.from_bytes(payload)
                tx_id = envelope.transaction_id
                if not tx_id or not envelope.sender_id or not envelope.signature or not envelope.stix_bundle_compressed:
                    await self.send_nack(writer, tx_id, NackReason.MALFORMED)
                    return
            except Exception:
                await self.send_nack(writer, tx_id, NackReason.MALFORMED)
                return

            # 3. Identity cross-check
            agency = self.trust_store.get_agency(envelope.sender_id)
            if not agency:
                await self.send_nack(writer, tx_id, NackReason.UNKNOWN_SENDER)
                return

            expected_tls_fp = agency['tls_certificate_fingerprint']
            if expected_tls_fp != peer_fingerprint:
                await self.send_nack(writer, tx_id, NackReason.IDENTITY_MISMATCH)
                return
            
            # Check revocation
            if self.trust_store.is_revoked(peer_fingerprint) or self.trust_store.is_revoked(agency['payload_signing_public_key_fingerprint']):
                await self.send_nack(writer, tx_id, NackReason.REVOKED_CERT)
                return

            # 4. ML-DSA verification
            pubkey_path = agency['payload_signing_public_key_path']
            is_valid = self.verifier.verify_signature(
                envelope.stix_bundle_compressed,
                envelope.signature,
                pubkey_path
            )
            if not is_valid:
                await self.send_nack(writer, tx_id, NackReason.SIG_INVALID)
                return
            
            t_verified = time.time_ns()

            # 5. Inbound PEP
            pep_allow, _ = self.pep.evaluate(envelope.sender_id, envelope.recipient_id, envelope.tlp_marking.value)
            if not pep_allow:
                await self.send_nack(writer, tx_id, NackReason.POLICY_DENIED)
                return

            # 6. Decompression
            try:
                stix_bytes = zlib.decompress(envelope.stix_bundle_compressed)
            except Exception:
                await self.send_nack(writer, tx_id, NackReason.MALFORMED)
                return

            # 7. STIX 2.1 Validation
            try:
                stix_bundle = json.loads(stix_bytes.decode('utf-8'))
                if stix_bundle.get('type') != 'bundle' or 'objects' not in stix_bundle:
                    await self.send_nack(writer, tx_id, NackReason.MALFORMED)
                    return
            except Exception:
                await self.send_nack(writer, tx_id, NackReason.MALFORMED)
                return

            # 8. OpenCTI Ingestion
            ingested = await self.ingestor.ingest_bundle(stix_bundle)
            if not ingested:
                await self.send_nack(writer, tx_id, NackReason.INGEST_FAILED)
                return

            t_ingested = time.time_ns()

            # 9. ACK
            await self.send_ack(writer, tx_id)
            
            from gateway_b.observability.telemetry_logger import log_telemetry_b
            log_telemetry_b(tx_id, t_received, t_verified, t_ingested, "ACKED")
            
        except Exception as e:
            traceback.print_exc()
            await self.send_nack(writer, tx_id, NackReason.MALFORMED)
