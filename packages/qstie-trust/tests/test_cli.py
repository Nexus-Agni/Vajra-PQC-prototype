import subprocess
import os
import pytest

PKI_DIR = "/app/pki_cli_test"

def run_cmd(cmd, check=True):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if check:
        assert res.returncode == 0, f"Command failed: {res.stderr}"
    return res

def test_cli_init_root():
    os.makedirs(PKI_DIR, exist_ok=True)
    run_cmd(["qstie-ca", "init-root", "--out-dir", f"{PKI_DIR}/ca", "--validity-days", "3650"])
    assert os.path.exists(f"{PKI_DIR}/ca/root_ca.crt")
    assert os.path.exists(f"{PKI_DIR}/ca/root_ca.key")

def test_cli_issue_gateway_cert():
    run_cmd(["qstie-ca", "issue-gateway-cert", "--agency-id", "RAW", "--ca-dir", f"{PKI_DIR}/ca", "--san", "gateway-a.internal", "--out-dir", f"{PKI_DIR}/gateway_raw"])
    assert os.path.exists(f"{PKI_DIR}/gateway_raw/raw_gateway.crt")
    assert os.path.exists(f"{PKI_DIR}/gateway_raw/raw_gateway.key")

def test_cli_issue_signing_key():
    run_cmd(["qstie-ca", "issue-signing-key", "--agency-id", "RAW", "--out-dir", f"{PKI_DIR}/gateway_raw"])
    assert os.path.exists(f"{PKI_DIR}/gateway_raw/raw_ml_dsa65.pem")
    assert os.path.exists(f"{PKI_DIR}/gateway_raw/raw_ml_dsa65.pub")

def test_cli_export_trust_bundle():
    run_cmd(["qstie-ca", "export-trust-bundle", "--agencies", "RAW", "--pki-root", PKI_DIR, "--out", f"{PKI_DIR}/trust_store.yaml"])
    assert os.path.exists(f"{PKI_DIR}/trust_store.yaml")

def test_cli_revoke():
    run_cmd(["qstie-ca", "revoke", "--agency-id", "RAW", "--key-type", "tls_cert", "--reason", "test_reason", "--out", f"{PKI_DIR}/revocation_list.yaml", "--fingerprint", "123"])
    assert os.path.exists(f"{PKI_DIR}/revocation_list.yaml")

def test_cli_missing_args():
    res = run_cmd(["qstie-ca", "init-root"], check=False)
    assert res.returncode != 0

def test_cli_invalid_ca_dir():
    res = run_cmd(["qstie-ca", "issue-gateway-cert", "--agency-id", "RAW", "--ca-dir", f"{PKI_DIR}/nonexistent", "--san", "a", "--out-dir", f"{PKI_DIR}/gateway_raw"], check=False)
    assert res.returncode != 0
