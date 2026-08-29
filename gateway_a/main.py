import asyncio
import logging
import signal
from concurrent.futures import ThreadPoolExecutor

from gateway_a.config import GatewayAConfig
from gateway_a.ingestion.misp_listener import MispZmqListener
from gateway_a.ingestion.stix_extractor import StixExtractor
from gateway_a.crypto.signer import MlDsaSigner
from gateway_a.crypto.tls_client import PqcTlsClient
from gateway_a.pipeline.signer_worker import SignerWorker
from gateway_a.pipeline.pep_worker import PepWorker
from gateway_a.pipeline.transmission_worker import TransmissionWorker
from gateway_a.pipeline.dead_letter import DeadLetterStore
from gateway_a.policy.pep_outbound import OutboundPep, SharingPolicyRule
from gateway_a.observability.metrics import MetricsServer
from qstie_common.enums.protocol_enums import TlpMarking

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_pipeline():
    config = GatewayAConfig()
    
    in_queue = asyncio.Queue(maxsize=config.ingestion_queue_maxsize)
    extracted_queue = asyncio.Queue(maxsize=config.extracted_queue_maxsize)
    signed_queue = asyncio.Queue(maxsize=config.signed_queue_maxsize)
    tx_queue = asyncio.Queue(maxsize=config.tx_queue_maxsize)
    
    thread_pool = ThreadPoolExecutor(max_workers=4)
    dlq = DeadLetterStore(filepath="results/phase4/dead_letter.jsonl")
    metrics = MetricsServer(port=8000)
    metrics.start()
    
    misp_listener = MispZmqListener(config.misp_zmq_endpoint, config.misp_tags_filter, in_queue)
    stix_extractor = StixExtractor(in_queue, extracted_queue, thread_pool)
    
    signer = MlDsaSigner(config.ml_dsa_private_key_path)
    signer_worker = SignerWorker(extracted_queue, signed_queue, signer, config.cert_path)
    
    policy_table = [
        SharingPolicyRule(tlp_marking=TlpMarking.AMBER, allowed_recipients={"NIA"}),
        SharingPolicyRule(tlp_marking=TlpMarking.AMBER_STRICT, allowed_recipients=set()),
        SharingPolicyRule(tlp_marking=TlpMarking.GREEN, allowed_recipients={"NIA", "ALLY_X"})
    ]
    pep = OutboundPep(policy_table)
    pep_worker = PepWorker(signed_queue, tx_queue, dlq, pep)
    
    tls_client = PqcTlsClient(config.cert_path, config.key_path, config.ca_trust_path)
    tx_worker = TransmissionWorker(tx_queue, tls_client, config, dlq)
    
    tasks = [
        asyncio.create_task(misp_listener.start()),
        asyncio.create_task(stix_extractor.start()),
        asyncio.create_task(signer_worker.start()),
        asyncio.create_task(pep_worker.start()),
        asyncio.create_task(tx_worker.start()),
    ]
    
    logger.info("Gateway A started successfully")
    
    stop_event = asyncio.Event()
    def handle_shutdown():
        logger.info("Initiating shutdown...")
        misp_listener.stop()
        stix_extractor.stop()
        signer_worker.stop()
        pep_worker.stop()
        tx_worker.stop()
        stop_event.set()
        
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_shutdown)
        except NotImplementedError:
            pass # Windows
            
    await stop_event.wait()
    await asyncio.gather(*tasks, return_exceptions=True)
    thread_pool.shutdown(wait=True)
    logger.info("Gateway A shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(run_pipeline())
    except KeyboardInterrupt:
        pass
