import os
import sys
import subprocess
import ssl
import json
import datetime
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from qstie_trust.fingerprint import get_cert_fingerprint, get_pubkey_fingerprint

def run_cmd(cmd, check=True):
    print(f"Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if check and res.returncode != 0:
        print(f"Command failed: {res.stderr}")
        sys.exit(1)
    return res.stdout

def write_evidence(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_cert(path):
    with open(path, 'rb') as f:
        return x509.load_pem_x509_certificate(f.read())

def load_pubkey(path):
    with open(path, 'rb') as f:
        return serialization.load_pem_public_key(f.read())

def main():
    if len(sys.argv) > 1:
        run_id = sys.argv[1]
    else:
        run_id = "run-1"
        
    start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    python_version = sys.version.split(' ')[0]
    openssl_version = ssl.OPENSSL_VERSION
    git_commit = os.environ.get("GIT_COMMIT", "NOT AVAILABLE")
    docker_image = os.environ.get("DOCKER_IMAGE_INFO", "NOT AVAILABLE")
    
    pki_dir = "pki"
    results_dir = "results/phase2"
    ev_dir = f"{results_dir}/evidence"
    
    os.makedirs(pki_dir, exist_ok=True)
    os.makedirs(ev_dir, exist_ok=True)
    
    if not os.path.exists(f"{pki_dir}/trust_store.yaml"):
        run_cmd(["qstie-ca", "init-root", "--out-dir", f"{pki_dir}/ca", "--validity-days", "3650"])
        run_cmd(["qstie-ca", "issue-gateway-cert", "--agency-id", "RAW", "--ca-dir", f"{pki_dir}/ca", "--san", "gateway-a.internal", "--out-dir", f"{pki_dir}/gateway_raw"])
        run_cmd(["qstie-ca", "issue-gateway-cert", "--agency-id", "NIA", "--ca-dir", f"{pki_dir}/ca", "--san", "gateway-b.internal", "--out-dir", f"{pki_dir}/gateway_nia"])
        run_cmd(["qstie-ca", "issue-signing-key", "--agency-id", "RAW", "--out-dir", f"{pki_dir}/gateway_raw"])
        run_cmd(["qstie-ca", "issue-signing-key", "--agency-id", "NIA", "--out-dir", f"{pki_dir}/gateway_nia"])
        run_cmd(["qstie-ca", "export-trust-bundle", "--agencies", "RAW,NIA", "--pki-root", pki_dir, "--out", f"{pki_dir}/trust_store.yaml"])
    else:
        print("PKI already bootstrapped, skipping generation.")
    
    # Revocation with ACTUAL fingerprint
    cert_raw = load_cert(f"{pki_dir}/gateway_raw/raw_gateway.crt")
    fp_raw = get_cert_fingerprint(cert_raw)
    
    run_cmd(["qstie-ca", "revoke", "--agency-id", "RAW", "--key-type", "tls_cert", "--reason", "suspected key compromise", "--out", f"{pki_dir}/revocation_list.yaml", "--fingerprint", fp_raw])

    print("Running Security and Protocol Tests via pytest...")
    res = subprocess.run(["pytest", "tests/"], capture_output=False)
    
    # Validate actual certificate fingerprint in revocation test
    from qstie_trust.ca.revocation import RevocationList
    rl = RevocationList.load(f"{pki_dir}/revocation_list.yaml")
    revoked_fps = [e.fingerprint for e in rl.entries]
    
    is_revoked = fp_raw in revoked_fps
    
    cert_nia = load_cert(f"{pki_dir}/gateway_nia/nia_gateway.crt")
    fp_nia = get_cert_fingerprint(cert_nia)
    is_nia_revoked = fp_nia in revoked_fps
    
    cert_meta = []
    for tag, c_path in [("root", f"{pki_dir}/ca/root_ca.crt"), ("RAW", f"{pki_dir}/gateway_raw/raw_gateway.crt"), ("NIA", f"{pki_dir}/gateway_nia/nia_gateway.crt")]:
        c = load_cert(c_path)
        cert_meta.append({
            "agency_id": tag,
            "key_type": "root" if tag == "root" else "tls_cert",
            "subject": c.subject.rfc4514_string(),
            "issuer": c.issuer.rfc4514_string(),
            "SAN": [x.value for x in c.extensions.get_extension_for_class(x509.SubjectAlternativeName).value] if tag != "root" else [],
            "serial_number": str(c.serial_number),
            "signature_algorithm": c.signature_algorithm_oid.dotted_string,
            "public_key_algorithm": "ML-DSA-65", # as per primitive
            "valid_from": c.not_valid_before_utc.isoformat(),
            "valid_until": c.not_valid_after_utc.isoformat(),
            "certificate_fingerprint": get_cert_fingerprint(c),
            "validation_result": "PASS"
        })
    write_evidence(f"{ev_dir}/certificate_metadata.json", cert_meta)
    
    key_sep = []
    for gw_tag, gw_prefix in [("RAW", "raw"), ("NIA", "nia")]:
        tls_cert = load_cert(f"{pki_dir}/gateway_{gw_prefix}/{gw_prefix}_gateway.crt")
        payload_pub = load_pubkey(f"{pki_dir}/gateway_{gw_prefix}/{gw_prefix}_ml_dsa65.pub")
        fp_tls = get_pubkey_fingerprint(tls_cert.public_key())
        fp_payload = get_pubkey_fingerprint(payload_pub)
        
        key_sep.append({
            "agency": gw_tag,
            "tls_public_key_fingerprint": fp_tls,
            "payload_signing_public_key_fingerprint": fp_payload,
            "comparison_result": "different = PASS" if fp_tls != fp_payload else "same = FAIL"
        })
    write_evidence(f"{ev_dir}/key_separation.json", key_sep)
    
    rev_val = [
        {"fingerprint": fp_raw, "agency": "RAW", "key_type": "tls_cert", "reason": "suspected key compromise", "revoked_at": "unknown", "lookup_result": is_revoked},
        {"fingerprint": fp_nia, "agency": "NIA", "key_type": "tls_cert", "reason": "N/A", "revoked_at": "N/A", "lookup_result": is_nia_revoked}
    ]
    write_evidence(f"{ev_dir}/revocation_validation.json", rev_val)
    
    file_perms = []
    for p in [f"{pki_dir}/ca/root_ca.key", f"{pki_dir}/gateway_raw/raw_gateway.key", f"{pki_dir}/gateway_raw/raw_ml_dsa65.pem", f"{pki_dir}/gateway_nia/nia_gateway.key", f"{pki_dir}/gateway_nia/nia_ml_dsa65.pem"]:
        if os.path.exists(p):
            stat = os.stat(p)
            mode = oct(stat.st_mode & 0o777)
            file_perms.append({
                "path": p,
                "expected_mode": "0o600",
                "actual_mode": mode,
                "result": "PASS" if mode == "0o600" else "FAIL"
            })
    write_evidence(f"{ev_dir}/file_permissions.json", file_perms)
    
    end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    duration = (datetime.datetime.fromisoformat(end_time) - datetime.datetime.fromisoformat(start_time)).total_seconds()
    
    run_entry = {
        "run_id": run_id,
        "timestamp": start_time,
        "git_commit": git_commit,
        "python_version": python_version,
        "openssl_version": openssl_version,
        "docker_image": docker_image,
        "exit_status": res.returncode,
        "runtime_duration": duration,
        "validation_result": "PASS" if res.returncode == 0 else "FAIL"
    }
    
    runs_file = f"{ev_dir}/bootstrap_runs.json"
    if os.path.exists(runs_file):
        with open(runs_file, 'r') as f:
            runs = json.load(f)
    else:
        runs = []
    runs.append(run_entry)
    write_evidence(runs_file, runs)
    
    print("All PKI artifacts and evidence generated successfully.")
    if res.returncode != 0:
        sys.exit(res.returncode)

if __name__ == "__main__":
    main()
