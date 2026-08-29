import json
import os
from collections import deque
import logging

logger = logging.getLogger(__name__)

class DeadLetterStore:
    def __init__(self, maxlen: int = 500, filepath: str = "results/phase4/dead_letter.jsonl"):
        self.maxlen = maxlen
        self.filepath = filepath
        self.store = deque(maxlen=maxlen)
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def add(self, transaction, reason: str) -> None:
        entry = {
            "transaction_id": str(transaction.transaction_id),
            "reason": reason,
            "state": transaction.state.value if hasattr(transaction.state, 'value') else str(transaction.state),
            "timestamp": transaction.created_at.isoformat()
        }
        self.store.append(entry)
        
        try:
            with open(self.filepath, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to dead letter file: {e}")
            
        logger.info(f"Transaction {transaction.transaction_id} dead-lettered. Reason: {reason}")

    def snapshot(self) -> list:
        return list(self.store)
