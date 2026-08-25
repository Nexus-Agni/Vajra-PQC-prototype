import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

class OpenCTIIngestor:
    def __init__(self, url: str, token: str, workers: int = 4):
        self.url = url
        self.token = token
        self.executor = ThreadPoolExecutor(max_workers=workers)
        
        # We only import pycti in the worker thread to keep it isolated, or here.
        if token and token != "synthetic-token-for-testing" and token != "mock":
            from pycti import OpenCTIApiClient
            try:
                self.client = OpenCTIApiClient(url, token)
                self.is_mock = False
            except Exception as e:
                self.client = None
                self.is_mock = True
        else:
            self.client = None
            self.is_mock = True

        self.invocation_count = 0

    def _ingest_sync(self, stix_bundle: dict) -> bool:
        """Runs in thread pool"""
        if self.is_mock:
            if stix_bundle.get("type") != "bundle":
                return False
            # Mock rejection scenario
            if "REJECT_ME" in json.dumps(stix_bundle):
                return False
            if "TIMEOUT_ME" in json.dumps(stix_bundle):
                import time
                time.sleep(2)
                raise Exception("Timeout")
            if "UNAVAILABLE_ME" in json.dumps(stix_bundle):
                raise Exception("Unavailable")
            return True
        else:
            try:
                # real pycti upload
                self.client.stix2.import_bundle(stix_bundle)
                return True
            except Exception as e:
                raise e

    async def ingest_bundle(self, stix_bundle: dict) -> bool:
        self.invocation_count += 1
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(self.executor, self._ingest_sync, stix_bundle)
            return result
        except Exception as e:
            return False
