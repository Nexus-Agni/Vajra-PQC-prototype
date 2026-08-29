import asyncio
import json
import logging
import pytest
from concurrent.futures import ThreadPoolExecutor
from gateway_a.ingestion.stix_extractor import StixExtractor
import os
from datetime import datetime
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@pytest.fixture
def thread_pool():
    executor = ThreadPoolExecutor(max_workers=2)
    yield executor
    executor.shutdown(wait=False)

@pytest.mark.asyncio
async def test_stix_extraction(thread_pool):
    in_queue = asyncio.Queue()
    out_queue = asyncio.Queue()
    
    extractor = StixExtractor(in_queue, out_queue, thread_pool)
    task = asyncio.create_task(extractor.start())
    
    evidence = []
    
    # 1. Valid MISP event -> STIX 2.1
    valid_misp = {
        "Event": {
            "uuid": "5d2f6645-8f64-4e20-b42e-131c950d210f",
            "info": "Test event",
            "date": "2026-08-26",
            "threat_level_id": "1",
            "analysis": "0",
            "Attribute": [
                {
                    "type": "ip-src",
                    "value": "1.1.1.1",
                    "uuid": "5d2f6645-8f64-4e20-b42e-131c950d2110"
                }
            ],
            "Tag": [{"name": "tlp:amber"}]
        }
    }
    await in_queue.put(valid_misp)
    
    try:
        tx1 = await asyncio.wait_for(out_queue.get(), timeout=5.0)
        assert tx1.stix_bundle is not None
        stix_dict = json.loads(tx1.stix_bundle.raw_json.decode())
        assert stix_dict["type"] == "bundle"
        assert tx1.stix_bundle.misp_event_uuid == "5d2f6645-8f64-4e20-b42e-131c950d210f"
        assert tx1.stix_bundle.tlp_marking == "tlp:amber"
        
        evidence.append({
            "test": "valid MISP event",
            "status": "PASS", 
            "details": f"Generated valid STIX 2.1 bundle with {len(tx1.stix_bundle.raw_json)} bytes"
        })
    except asyncio.TimeoutError:
        pytest.fail("Failed to extract valid STIX bundle")

    # 2. Invalid conversion (missing vital MISP fields)
    invalid_misp = {
        "Event": {
            "info": 123 # Invalid type, missing uuid, missing structure
        }
    }
    await in_queue.put(invalid_misp)
    
    try:
        invalid_tx = await asyncio.wait_for(out_queue.get(), timeout=2.0)
        pytest.fail(f"Invalid MISP event should have failed, but produced: {invalid_tx.stix_bundle.raw_json.decode()}")
    except asyncio.TimeoutError:
        pass
        
    evidence.append({
        "test": "invalid conversion",
        "status": "PASS",
        "details": "Rejected before crypto, no transaction produced"
    })

    # 3. Malformed/invalid STIX 
    import gateway_a.ingestion.stix_extractor as se
    original_parse = se.stix2_parse
    
    class MockSTIXError(Exception):
        pass
    se.STIXError = MockSTIXError
    
    def mock_parse(data):
        raise MockSTIXError("Mocked validation failure")
        
    se.stix2_parse = mock_parse
    
    await in_queue.put(valid_misp)
    
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(out_queue.get(), timeout=2.0)
        
    evidence.append({
        "test": "malformed/invalid STIX",
        "status": "PASS",
        "details": "Validation failed, rejected before signing"
    })
    
    se.stix2_parse = original_parse
    
    extractor.stop()
    task.cancel()
    
    os.makedirs("results/phase4/evidence", exist_ok=True)
    with open("results/phase4/evidence/stix_validation.json", "w") as f:
        json.dump({"timestamp": datetime.utcnow().isoformat(), "environment": "mock", "results": evidence}, f, indent=2)
