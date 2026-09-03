"""Benchmark campaign configuration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class CryptoConfig:
    """PKI certificate paths for a given crypto mode."""
    group: str
    a_cert_path: str
    a_key_path: str
    a_payload_key_path: str
    a_ca_trust_path: str
    b_cert_path: str
    b_key_path: str
    b_ca_trust_path: str
    trust_store_path: str


# Pre-defined crypto configurations matching the compose environment.
CLASSICAL = CryptoConfig(
    group="X25519",
    a_cert_path="pki/gateway_raw/raw_gateway_ecdsa.crt",
    a_key_path="pki/gateway_raw/raw_gateway_ecdsa.key",
    a_payload_key_path="pki/gateway_raw/raw_ecdsa256.pem",
    a_ca_trust_path="pki/ca_ecdsa/root_ca.crt",
    b_cert_path="pki/gateway_nia/nia_gateway_ecdsa.crt",
    b_key_path="pki/gateway_nia/nia_gateway_ecdsa.key",
    b_ca_trust_path="pki/ca_ecdsa/root_ca.crt",
    trust_store_path="pki/trust_store_classical.yaml",
)

HYBRID_PQC = CryptoConfig(
    group="X25519MLKEM768",
    a_cert_path="pki/gateway_raw/raw_gateway.crt",
    a_key_path="pki/gateway_raw/raw_gateway.key",
    a_payload_key_path="pki/gateway_raw/raw_ml_dsa65.pem",
    a_ca_trust_path="pki/ca/root_ca.crt",
    b_cert_path="pki/gateway_nia/nia_gateway.crt",
    b_key_path="pki/gateway_nia/nia_gateway.key",
    b_ca_trust_path="pki/ca/root_ca.crt",
    trust_store_path="pki/trust_store.yaml",
)


@dataclass
class BenchmarkConfig:
    """Top-level benchmark campaign configuration."""

    crypto_configs: List[CryptoConfig] = field(
        default_factory=lambda: [CLASSICAL, HYBRID_PQC]
    )
    network_profiles: List[str] = field(
        default_factory=lambda: ["stable", "adverse"]
    )
    event_count: int = 50
    wait_seconds: int = 30
    evidence_dir: str = "/app/results/phase5/evidence"
    telemetry_a_path: str = "/app/results/phase5/evidence/telemetry_a.jsonl"
    telemetry_b_path: str = "/app/results/phase5/evidence/telemetry_b.jsonl"
    compose_file: str = "/app/compose.yaml"
