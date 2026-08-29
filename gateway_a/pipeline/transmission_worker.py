import asyncio
import logging

from gateway_a.crypto.tls_client import PqcTlsClient
from gateway_a.models import GatewayATransaction, TransactionState
from gateway_a.config import GatewayAConfig

logger = logging.getLogger(__name__)

class TransmissionWorker:
    def __init__(self, tx_queue: asyncio.Queue, tls_client: PqcTlsClient, config: GatewayAConfig, dead_letter_store):
        self.tx_queue = tx_queue
        self.tls_client = tls_client
        self.config = config
        self.dead_letter_store = dead_letter_store
        self.running = False

    async def start(self):
        self.running = True
        while self.running:
            try:
                transaction: GatewayATransaction = await self.tx_queue.get()
                await self._process_transaction(transaction)
                self.tx_queue.task_done()
            except asyncio.CancelledError:
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in TransmissionWorker loop: {e}")

    async def _process_transaction(self, transaction: GatewayATransaction):
        recipient_config = self.config.recipients.get(transaction.recipient_id)
        if not recipient_config:
            transaction.state = TransactionState.FAILED
            self.dead_letter_store.add(transaction, "UNKNOWN_RECIPIENT_ROUTING")
            return

        host = recipient_config["host"]
        port = int(recipient_config["port"])

        max_attempts = self.config.max_attempts
        base_delay = self.config.base_backoff_ms / 1000.0
        
        while transaction.retry_count < max_attempts:
            transaction.retry_count += 1
            transaction.state = TransactionState.SENDING
            
            try:
                session = await self.tls_client.open_session(host, port)
            except Exception as e:
                # TLS failure (timeout, connection refused, wrong CA, etc)
                logger.error(f"TLS failure on attempt {transaction.retry_count}: {e}")
                if transaction.retry_count < max_attempts:
                    delay = base_delay * (self.config.backoff_factor ** (transaction.retry_count - 1))
                    await asyncio.sleep(delay)
                    continue
                else:
                    transaction.state = TransactionState.FAILED
                    self.dead_letter_store.add(transaction, "MAX_RETRIES_EXCEEDED")
                    return

            success, reason = await session.send_envelope(transaction)
            await session.close()
            
            if success:
                transaction.state = TransactionState.ACKED
                logger.info(f"Transaction {transaction.transaction_id} ACKED.")
                return
            else:
                if reason in ["TIMEOUT", "TRANSPORT_ERROR", "CONNECTION_REFUSED"]:
                    logger.warning(f"Transport failure '{reason}' on attempt {transaction.retry_count}")
                    if transaction.retry_count < max_attempts:
                        delay = base_delay * (self.config.backoff_factor ** (transaction.retry_count - 1))
                        await asyncio.sleep(delay)
                        continue
                    else:
                        transaction.state = TransactionState.FAILED
                        self.dead_letter_store.add(transaction, "MAX_RETRIES_EXCEEDED")
                        return
                else:
                    logger.warning(f"Transaction {transaction.transaction_id} NACKed: {reason}")
                    transaction.state = TransactionState.FAILED
                    self.dead_letter_store.add(transaction, f"NACK_{reason}")
                    return
    def stop(self):
        self.running = False
