import asyncio
import json
import logging
import pytest
import os
from datetime import datetime
import sys

from gateway_a.policy.pep_outbound import OutboundPep, SharingPolicyRule
from gateway_a.pipeline.pep_worker import PepWorker
from gateway_a.pipeline.dead_letter import DeadLetterStore
from gateway_a.models import GatewayATransaction, StixBundle, TransactionState
from qstie_common.enums.protocol_enums import TlpMarking

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@pytest.fixture
def pep():
    policy_table = [
        SharingPolicyRule(tlp_marking=TlpMarking.AMBER, allowed_recipients={"NIA"}),
        SharingPolicyRule(tlp_marking=TlpMarking.AMBER_STRICT, allowed_recipients=set()),
        SharingPolicyRule(tlp_marking=TlpMarking.GREEN, allowed_recipients={"NIA", "ALLY_X"})
    ]
    return OutboundPep(policy_table)

@pytest.mark.asyncio
async def test_outbound_pep(pep):
    in_queue = asyncio.Queue()
    out_queue = asyncio.Queue()
    dlq = DeadLetterStore()
    
    worker = PepWorker(in_queue, out_queue, dlq, pep)
    task = asyncio.create_task(worker.start())
    
    evidence = []
    
    def create_tx(tlp, recipient):
        bundle = StixBundle("b1", b"{}", tlp, "m1")
        return GatewayATransaction(stix_bundle=bundle, recipient_id=recipient, state=TransactionState.SIGNED)
        
    # 1. Allow: TLP AMBER + NIA
    tx1 = create_tx(TlpMarking.AMBER, "NIA")
    await in_queue.put(tx1)
    out_tx1 = await asyncio.wait_for(out_queue.get(), timeout=2.0)
    assert out_tx1.state == TransactionState.POLICY_APPROVED
    evidence.append({"test": "allow valid TLP and recipient", "status": "PASS", "details": "AMBER + NIA allowed"})
    
    # 2. Deny: Boundary TLP AMBER_STRICT + NIA
    tx2 = create_tx(TlpMarking.AMBER_STRICT, "NIA")
    await in_queue.put(tx2)
    # Should not produce to out_queue
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(out_queue.get(), timeout=1.0)
    assert tx2.state == TransactionState.POLICY_REJECTED
    assert len(dlq.snapshot()) == 1
    evidence.append({"test": "deny boundary TLP", "status": "PASS", "details": "AMBER_STRICT + NIA denied"})
    
    # 3. Unknown recipient: TLP GREEN + UNKNOWN
    tx3 = create_tx(TlpMarking.GREEN, "UNKNOWN")
    await in_queue.put(tx3)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(out_queue.get(), timeout=1.0)
    assert tx3.state == TransactionState.POLICY_REJECTED
    evidence.append({"test": "unknown recipient", "status": "PASS", "details": "GREEN + UNKNOWN denied"})

    # 4. Unknown TLP (if such a thing was somehow injected)
    # We will bypass the enum typing temporarily
    tx4 = create_tx("tlp:red", "NIA")
    await in_queue.put(tx4)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(out_queue.get(), timeout=1.0)
    assert tx4.state == TransactionState.POLICY_REJECTED
    evidence.append({"test": "boundary TLP values (unknown)", "status": "PASS", "details": "tlp:red denied"})
    
    worker.stop()
    task.cancel()
    
    os.makedirs("results/phase4/evidence", exist_ok=True)
    with open("results/phase4/evidence/policy_validation.json", "w") as f:
        json.dump({"timestamp": datetime.utcnow().isoformat(), "environment": "mock", "results": evidence}, f, indent=2)
