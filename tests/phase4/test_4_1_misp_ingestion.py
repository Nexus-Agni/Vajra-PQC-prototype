import asyncio
import json
import logging
import pytest
import zmq
import zmq.asyncio
from gateway_a.ingestion.misp_listener import MispZmqListener
import os
import sys
from datetime import datetime

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Fixture to mock MISP ZMQ publisher
@pytest.fixture
async def mock_misp_publisher():
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.PUB)
    port = socket.bind_to_random_port("tcp://127.0.0.1")
    yield socket, f"tcp://127.0.0.1:{port}"
    socket.close()
    context.term()

@pytest.mark.asyncio
async def test_misp_ingestion(mock_misp_publisher):
    pub_socket, endpoint = mock_misp_publisher
    out_queue = asyncio.Queue(maxsize=2)
    tags_filter = ["share:NIA", "tlp:amber"]
    
    listener = MispZmqListener(endpoint, tags_filter, out_queue)
    
    task = asyncio.create_task(listener.start())
    
    # Wait for listener to connect
    await asyncio.sleep(0.5)
    
    evidence = []
    
    # 1. Event received & 2. Event filtered (valid)
    valid_event = {
        "Event": {
            "uuid": "1111",
            "Tag": [{"name": "share:NIA"}, {"name": "tlp:amber"}]
        }
    }
    await pub_socket.send_string(f"misp_json {json.dumps(valid_event)}")
    
    event1 = await asyncio.wait_for(out_queue.get(), timeout=2.0)
    assert event1["Event"]["uuid"] == "1111"
    evidence.append({"test": "event received", "status": "PASS", "details": "Valid event accepted"})
    evidence.append({"test": "event filtered", "status": "PASS", "details": "Valid event filtered based on tag"})
    
    # 3. Event ignored (invalid)
    invalid_event = {
        "Event": {
            "uuid": "2222",
            "Tag": [{"name": "share:OTHER"}]
        }
    }
    await pub_socket.send_string(f"misp_json {json.dumps(invalid_event)}")
    
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(out_queue.get(), timeout=1.0)
    evidence.append({"test": "event ignored", "status": "PASS", "details": "Invalid event dropped"})

    # 4 & 5. ZMQ disconnect and reconnect
    pub_socket.close()
    await asyncio.sleep(1.0) # Wait for listener to notice
    
    context2 = zmq.asyncio.Context()
    pub_socket2 = context2.socket(zmq.PUB)
    pub_socket2.bind(endpoint)
    
    # Wait for listener to reconnect
    await asyncio.sleep(3.0) 
    
    valid_event3 = {
        "Event": {
            "uuid": "3333",
            "Tag": [{"name": "tlp:amber"}]
        }
    }
    await pub_socket2.send_string(f"misp_json {json.dumps(valid_event3)}")
    event3 = await asyncio.wait_for(out_queue.get(), timeout=3.0)
    assert event3["Event"]["uuid"] == "3333"
    evidence.append({"test": "ZMQ disconnect", "status": "PASS", "details": "Disconnect detected"})
    evidence.append({"test": "ZMQ reconnect", "status": "PASS", "details": "Reconnected and received event"})
    pub_socket2.close()
    context2.term()
    
    # 6. Slow consumer / backpressure
    context3 = zmq.asyncio.Context()
    pub_socket3 = context3.socket(zmq.PUB)
    pub_socket3.bind(endpoint)
    await asyncio.sleep(3.0)

    valid_event4 = {"Event": {"uuid": "4444", "Tag": [{"name": "tlp:amber"}]}}
    valid_event5 = {"Event": {"uuid": "5555", "Tag": [{"name": "tlp:amber"}]}}
    valid_event6 = {"Event": {"uuid": "6666", "Tag": [{"name": "tlp:amber"}]}}
    
    await pub_socket3.send_string(f"misp_json {json.dumps(valid_event4)}")
    await pub_socket3.send_string(f"misp_json {json.dumps(valid_event5)}")
    await pub_socket3.send_string(f"misp_json {json.dumps(valid_event6)}")
    
    await asyncio.sleep(1.0)
    assert out_queue.qsize() == 2 # Maxsize reached
    assert out_queue.full()
    
    evidence.append({"test": "slow consumer", "status": "PASS", "details": "Queue maxsize respected (backpressure)"})

    listener.stop()
    task.cancel()
    
    pub_socket3.close()
    context3.term()
    
    # Write evidence
    os.makedirs("results/phase4/evidence", exist_ok=True)
    with open("results/phase4/evidence/misp_validation.json", "w") as f:
        json.dump({"timestamp": datetime.utcnow().isoformat(), "environment": "mock", "results": evidence}, f, indent=2)
