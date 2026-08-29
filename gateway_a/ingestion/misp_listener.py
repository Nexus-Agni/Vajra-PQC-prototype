import asyncio
import json
import logging
import zmq
import zmq.asyncio
from typing import Set

logger = logging.getLogger(__name__)

class MispZmqListener:
    def __init__(self, endpoint: str, tags_filter: list[str], out_queue: asyncio.Queue):
        self.endpoint = endpoint
        self.tags_filter = set(tags_filter) if tags_filter else set()
        self.out_queue = out_queue
        self.context = zmq.asyncio.Context()
        self.running = False
        self._socket = None

    async def start(self):
        self.running = True
        while self.running:
            try:
                self._socket = self.context.socket(zmq.SUB)
                self._socket.connect(self.endpoint)
                self._socket.setsockopt_string(zmq.SUBSCRIBE, "misp_json")
                
                logger.info(f"Connected to MISP ZMQ at {self.endpoint}")

                while self.running:
                    # Async receive
                    message = await self._socket.recv_string()
                    topic, _, payload = message.partition(" ")
                    
                    if topic != "misp_json":
                        continue
                        
                    try:
                        event_data = json.loads(payload)
                        if self._is_relevant(event_data):
                            # Block if queue is full (backpressure)
                            await self.out_queue.put(event_data)
                            logger.debug("Enqueued relevant MISP event")
                        else:
                            logger.debug("Ignored irrelevant MISP event")
                    except json.JSONDecodeError:
                        logger.error("Failed to decode MISP event payload")
                        
            except asyncio.CancelledError:
                self.running = False
                break
            except zmq.ZMQError as e:
                logger.error(f"ZMQ Error: {e}, reconnecting...")
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Unexpected error in MISP listener: {e}")
                await asyncio.sleep(2)
            finally:
                if self._socket:
                    self._socket.close()

    def stop(self):
        self.running = False
        if self._socket:
            self._socket.close()
        self.context.term()
        
    def _is_relevant(self, event_data: dict) -> bool:
        if not self.tags_filter:
            return True 
            
        event = event_data.get("Event", {})
        if not event:
            return False
            
        tags = event.get("Tag", [])
        event_tag_names = {tag.get("name") for tag in tags}
        
        return bool(self.tags_filter.intersection(event_tag_names))
