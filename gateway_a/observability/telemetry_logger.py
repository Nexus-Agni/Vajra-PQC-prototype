import json
import os
import time

TELEMETRY_FILE = "results/phase5/evidence/telemetry_a.jsonl"

def log_telemetry(transaction):
    # Log the telemetry of a transaction
    try:
        data = {
            "transaction_id": str(transaction.transaction_id),
            "state": transaction.state.value,
            "telemetry": transaction.telemetry
        }
        with open(TELEMETRY_FILE, "a") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to log telemetry: {e}")
