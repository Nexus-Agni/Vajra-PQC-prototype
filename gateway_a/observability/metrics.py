from prometheus_client import Counter, Gauge, Histogram, start_http_server
import logging

logger = logging.getLogger(__name__)

class MetricsServer:
    def __init__(self, port: int = 8000):
        self.port = port
        
        self.tx_processed = Counter('qstie_gateway_a_tx_processed_total', 'Total transactions processed')
        self.tx_failed = Counter('qstie_gateway_a_tx_failed_total', 'Total transactions failed', ['reason'])
        
        self.queue_depth_misp = Gauge('qstie_gateway_a_queue_depth_misp', 'Depth of MISP queue')
        self.queue_depth_extracted = Gauge('qstie_gateway_a_queue_depth_extracted', 'Depth of extracted queue')
        self.queue_depth_signed = Gauge('qstie_gateway_a_queue_depth_signed', 'Depth of signed queue')
        self.queue_depth_tx = Gauge('qstie_gateway_a_queue_depth_tx', 'Depth of transmission queue')
        
        self.processing_time = Histogram('qstie_gateway_a_processing_time_seconds', 'Time spent processing a transaction')

    def start(self):
        try:
            start_http_server(self.port)
            logger.info(f"Metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server on port {self.port}: {e}")
