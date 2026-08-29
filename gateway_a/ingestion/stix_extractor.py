import asyncio
import json
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from gateway_a.models import StixBundle, GatewayATransaction, TransactionState
from qstie_common.enums.protocol_enums import TlpMarking

try:
    from misp_stix_converter import MISPtoSTIX21Parser
except ImportError:
    MISPtoSTIX21Parser = None
    
try:
    from stix2 import parse as stix2_parse
    from stix2.exceptions import STIXError
except ImportError:
    stix2_parse = None
    STIXError = Exception

logger = logging.getLogger(__name__)

class StixExtractor:
    def __init__(self, in_queue: asyncio.Queue, out_queue: asyncio.Queue, executor: ThreadPoolExecutor):
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.executor = executor
        self.running = False
        
        if MISPtoSTIX21Parser is None or stix2_parse is None:
            logger.warning("misp-stix or stix2 library is not available. STIX extraction will fail.")

    async def start(self):
        self.running = True
        while self.running:
            try:
                misp_event = await self.in_queue.get()
                
                # Perform conversion and validation in executor
                bundle = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self._convert_and_validate,
                    misp_event
                )
                
                if bundle:
                    transaction = GatewayATransaction(
                        stix_bundle=bundle,
                        state=TransactionState.VALIDATED
                    )
                    await self.out_queue.put(transaction)
                    logger.debug(f"Successfully extracted and enqueued transaction for MISP event: {bundle.misp_event_uuid}")
                else:
                    logger.error("MISP event rejected before crypto due to conversion or validation failure.")
                    
                self.in_queue.task_done()
                
            except asyncio.CancelledError:
                self.running = False
                break
            except Exception as e:
                logger.error(f"Unexpected error in STIX Extractor: {e}")

    def stop(self):
        self.running = False

    def _convert_and_validate(self, misp_event: dict) -> Optional[StixBundle]:
        if MISPtoSTIX21Parser is None or stix2_parse is None:
            logger.error("Libraries missing")
            return None
            
        misp_event_uuid = misp_event.get("Event", {}).get("uuid", "")
        if not misp_event_uuid:
            logger.error("Invalid MISP event: missing Event.uuid")
            return None
            
        try:
            # 1. Convert to STIX 2.1
            parser = MISPtoSTIX21Parser()
            parser.parse_misp_event(misp_event)
            
            # Depending on misp_stix_converter version, it's either .stix_package or .bundle
            stix_package = getattr(parser, 'stix_package', None) or getattr(parser, 'bundle', None)
            
            if not stix_package:
                logger.error("STIX bundle generation failed (no package returned).")
                return None
                
            stix_bundle_str = stix_package.serialize()
            
            # 2. Validate using stix2
            parsed_bundle = stix2_parse(stix_bundle_str)
            
            # Extract basic info
            bundle_id = parsed_bundle.get("id", "bundle--unknown")
            misp_event_uuid = misp_event.get("Event", {}).get("uuid", "")
            
            tlp_marking = TlpMarking.AMBER
            for tag in misp_event.get("Event", {}).get("Tag", []):
                tag_name = tag.get("name", "").lower()
                if tag_name == "tlp:clear" or tag_name == "tlp:white":
                    tlp_marking = TlpMarking.GREEN
                elif tag_name == "tlp:green":
                    tlp_marking = TlpMarking.GREEN
                elif tag_name == "tlp:amber":
                    tlp_marking = TlpMarking.AMBER
                elif tag_name == "tlp:amber+strict":
                    tlp_marking = TlpMarking.AMBER_STRICT
            
            return StixBundle(
                bundle_id=bundle_id,
                raw_json=stix_bundle_str.encode('utf-8'),
                tlp_marking=tlp_marking,
                misp_event_uuid=misp_event_uuid
            )
            
        except STIXError as e:
            logger.error(f"STIX validation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"MISP to STIX conversion failed: {e}")
            return None
