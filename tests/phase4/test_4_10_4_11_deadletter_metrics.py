import os
import json
import pytest
from datetime import datetime
import requests
import time

from gateway_a.pipeline.dead_letter import DeadLetterStore
from gateway_a.observability.metrics import MetricsServer
from gateway_a.models import GatewayATransaction, StixBundle, TransactionState
from qstie_common.enums.protocol_enums import TlpMarking

def test_dead_letter_and_metrics(tmp_path):
    evidence_dl = []
    evidence_metrics = []
    
    # --- Dead Letter Test ---
    dl_file = tmp_path / "dead_letter.jsonl"
    store = DeadLetterStore(maxlen=5, filepath=str(dl_file))
    
    # Add 6 items (one should be evicted from deque but still in file)
    for i in range(6):
        bundle = StixBundle(f"b{i}", b"{}", TlpMarking.AMBER, f"m{i}")
        tx = GatewayATransaction(stix_bundle=bundle, recipient_id="NIA", state=TransactionState.FAILED)
        store.add(tx, f"REASON_{i}")
        
    snap = store.snapshot()
    assert len(snap) == 5
    assert snap[0]["reason"] == "REASON_1"  # 0 was evicted
    
    with open(dl_file, "r") as f:
        lines = f.readlines()
        
    assert len(lines) == 6
    assert json.loads(lines[0])["reason"] == "REASON_0"
    
    evidence_dl.append({"test": "file append and bounded deque", "status": "PASS", "details": f"Deque maxlen enforced (5), file contains all (6)"})
    
    # --- 1. Dead Letter Store Maxlen 500 test ---
    dlq_path = "results/phase4/test_dlq.jsonl"
    if os.path.exists(dlq_path):
        os.remove(dlq_path)
        
    # The requirement is maxlen=500
    dlq = DeadLetterStore(filepath=dlq_path, maxlen=500)
    
    def create_tx(tx_id):
        bundle = StixBundle(f"b_{tx_id}", b"{}", TlpMarking.AMBER, f"m_{tx_id}")
        tx = GatewayATransaction(stix_bundle=bundle, recipient_id="NIA", state=TransactionState.FAILED)
        tx.transaction_id = tx_id
        return tx

    # Insert 500 items
    for i in range(500):
        tx = create_tx(f"tx_{i}")
        dlq.add(tx, "FAIL")
        
    snapshot = dlq.snapshot()
    assert len(snapshot) == 500
    assert snapshot[0]["transaction_id"] == "tx_0"
    
    # Insert 501st item
    tx_501 = create_tx("tx_500")
    dlq.add(tx_501, "FAIL")
    
    snapshot2 = dlq.snapshot()
    assert len(snapshot2) == 500
    assert snapshot2[0]["transaction_id"] == "tx_1" # Oldest evicted
    assert snapshot2[-1]["transaction_id"] == "tx_500" # Newest retained
    
    evidence_dlq = [{
        "test": "dead-letter store maxlen 500 boundary",
        "status": "PASS",
        "details": "Inserted 501 items. Deque maintained maxlen=500, oldest item tx_0 evicted, newest item tx_500 retained. JSONL append-only verified."
    }]
    
    # Write evidence for deadletter
    os.makedirs("results/phase4/evidence", exist_ok=True)
    with open("results/phase4/evidence/deadletter_validation.json", "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "environment": "mock",
            "configured_maxlen": 500,
            "items_before_overflow": 500,
            "items_after_overflow": 500,
            "oldest_evicted": True,
            "newest_retained": True,
            "status": "PASS",
            "results": evidence_dlq
        }, f, indent=2)
    
    # --- Metrics Test ---
    # Metrics server uses a singleton registry in prometheus_client, so we should use a unique port
    server = MetricsServer(port=8001)
    server.start()
    
    server.tx_processed.inc()
    server.tx_failed.labels(reason='POLICY_REJECT').inc()
    server.queue_depth_tx.set(42)
    
    time.sleep(0.5) # Let server start
    resp = requests.get("http://127.0.0.1:8001/")
    assert resp.status_code == 200
    
    text = resp.text
    assert 'qstie_gateway_a_tx_processed_total' in text
    assert 'qstie_gateway_a_tx_failed_total' in text
    assert 'qstie_gateway_a_queue_depth_tx 42.0' in text
    
    evidence_metrics.append({"test": "prometheus metrics exposed", "status": "PASS"})
    
    with open("results/phase4/evidence/metrics_validation.json", "w") as f:
        json.dump({"timestamp": datetime.utcnow().isoformat(), "environment": "mock", "results": evidence_metrics}, f, indent=2)
