import struct
import asyncio
import logging
import json
from typing import Tuple

from qstie_common.enums.protocol_enums import MessageType
from gateway_a.models import GatewayATransaction
from qstie_common.models.envelope import TransactionEnvelope as ProtoTransactionEnvelope

logger = logging.getLogger(__name__)

class PqcSession:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer

    async def send_envelope(self, transaction: GatewayATransaction) -> Tuple[bool, str]:
        """
        Frames and sends the envelope; awaits ACK/NACK.
        Returns (success: bool, reason: str)
        """
        try:
            proto_env = ProtoTransactionEnvelope(
                transaction_id=str(transaction.transaction_id),
                sender_id=transaction.sender_id,
                recipient_id=transaction.recipient_id,
                tlp_marking=transaction.stix_bundle.tlp_marking,
                stix_bundle_compressed=transaction.stix_bundle_compressed,
                signature=transaction.signature,
                signer_cert_fingerprint=transaction.signer_cert_fingerprint,
                created_at_unix_ms=int(transaction.created_at.timestamp() * 1000)
            )
            payload = proto_env.to_bytes()
            
            # Frame: 1 byte msg_type + 4 bytes big-endian length + payload
            frame = struct.pack(">BI", MessageType.SIGNED_BUNDLE.value, len(payload)) + payload
            
            self.writer.write(frame)
            await self.writer.drain()
            
            # Wait for response (ACK/NACK)
            msg_type_byte = await asyncio.wait_for(self.reader.readexactly(1), timeout=5.0)
            msg_type = msg_type_byte[0]
            
            len_bytes = await asyncio.wait_for(self.reader.readexactly(4), timeout=5.0)
            payload_len = struct.unpack(">I", len_bytes)[0]
            
            resp_payload = await asyncio.wait_for(self.reader.readexactly(payload_len), timeout=5.0)
            
            if msg_type == MessageType.ACK.value:
                resp_dict = json.loads(resp_payload.decode('utf-8'))
                if resp_dict.get("transaction_id") == str(transaction.transaction_id):
                    return True, "ACK"
                return False, "ACK_ID_MISMATCH"
            elif msg_type == MessageType.NACK.value:
                resp_dict = json.loads(resp_payload.decode('utf-8'))
                return False, resp_dict.get("reason", "UNKNOWN_NACK")
            else:
                return False, "UNKNOWN_RESPONSE_TYPE"
                
        except asyncio.TimeoutError:
            return False, "TIMEOUT"
        except ConnectionRefusedError:
            return False, "CONNECTION_REFUSED"
        except Exception as e:
            logger.error(f"Error in send_envelope: {e}")
            return False, "TRANSPORT_ERROR"

    async def close(self) -> None:
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass
