import asyncio
import logging

from gateway_a.policy.pep_outbound import OutboundPep
from gateway_a.models import GatewayATransaction, TransactionState

logger = logging.getLogger(__name__)

class PepWorker:
    def __init__(self, in_queue: asyncio.Queue, out_queue: asyncio.Queue, dead_letter_store, pep: OutboundPep):
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.dead_letter_store = dead_letter_store
        self.pep = pep
        self.running = False

    async def start(self):
        self.running = True
        while self.running:
            try:
                transaction: GatewayATransaction = await self.in_queue.get()
                
                tlp = transaction.stix_bundle.tlp_marking
                recipient_id = transaction.recipient_id
                
                authorized, reason = self.pep.authorize(tlp, recipient_id)
                
                if authorized:
                    transaction.state = TransactionState.POLICY_APPROVED
                    await self.out_queue.put(transaction)
                    logger.debug(f"Transaction {transaction.transaction_id} policy approved for {recipient_id}")
                else:
                    transaction.state = TransactionState.POLICY_REJECTED
                    logger.warning(f"Transaction {transaction.transaction_id} policy rejected: {reason}")
                    if self.dead_letter_store:
                        self.dead_letter_store.add(transaction, reason)
                
                self.in_queue.task_done()
                
            except asyncio.CancelledError:
                self.running = False
                break
            except Exception as e:
                logger.error(f"Unexpected error in PepWorker: {e}")
                self.in_queue.task_done()

    def stop(self):
        self.running = False
