import ssl
import asyncio
import logging

logger = logging.getLogger(__name__)

class PqcTlsClient:
    def __init__(self, cert_path: str, key_path: str, ca_trust_path: str, hybrid_group: str = "X25519MLKEM768"):
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_trust_path = ca_trust_path
        self.hybrid_group = hybrid_group

    def create_ssl_context(self) -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        # Mutual TLS required
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = False
        context.load_verify_locations(cafile=self.ca_trust_path)

        context.load_cert_chain(certfile=self.cert_path, keyfile=self.key_path)
        
        # Phase-0 validated native compatibility shim for X25519MLKEM768
        return context

    async def open_session(self, host: str, port: int) -> "PqcSession":
        ssl_context = self.create_ssl_context()
        reader, writer = await asyncio.open_connection(
            host, port, ssl=ssl_context
        )
        # Using a late import or passing it back is fine.
        # Let's import PqcSession here to avoid circular imports.
        from gateway_a.transport.protocol import PqcSession
        return PqcSession(reader, writer)
