import json
import os
import time

TELEMETRY_FILE = "results/phase5/evidence/telemetry_b.jsonl"

def log_telemetry_b(tx_id, t_received, t_verified, t_ingested, state="ACKED"):
    try:
        data = {
            "transaction_id": tx_id,
            "state": state,
            "telemetry": {
                "t_received_b": t_received,
                "t_verified_b": t_verified,
                "t_ingested_b": t_ingested
            }
        }
        with open(TELEMETRY_FILE, "a") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to log telemetry: {e}")
