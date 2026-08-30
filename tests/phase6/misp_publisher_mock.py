import zmq
import time
import json
import sys

def publish_events(count=50, tlp='green'):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://0.0.0.0:50000")
    
    print(f"Mock MISP Publisher started on port 50000")
    # Wait for subscribers to connect
    time.sleep(5)
    
    for i in range(count):
        event = {
            "Event": {
                "id": str(i),
                "uuid": f"550e8400-e29b-41d4-a716-44665544{i:04d}",
                "info": f"Test event {i}",
                "Tag": [{"name": f"tlp:{tlp}"}],
                "Attribute": []
            }
        }
        msg = f"misp_json  {json.dumps(event)}"
        socket.send_string(msg)
        time.sleep(0.1)
        
    print(f"Published {count} events.")
    socket.close()
    context.term()

if __name__ == '__main__':
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    tlp = sys.argv[2] if len(sys.argv) > 2 else 'green'
    publish_events(count, tlp)
