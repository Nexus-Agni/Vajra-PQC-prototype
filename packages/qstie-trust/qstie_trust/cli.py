import argparse
import os
import sys
import datetime
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from qstie_trust.ca.root_ca import init_root, issue_leaf_cert, CertificateAuthority
from qstie_trust.ca.signing_keygen import generate_ml_dsa_keypair
from qstie_trust.ca.revocation import RevocationList
from qstie_trust.export import TrustBundleExporter
from qstie_trust.fingerprint import get_cert_fingerprint, get_pubkey_fingerprint
from qstie_trust.models import TrustBundleEntry, RevocationEntry

def save_private_key(key, path: str):
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(path, 'wb') as f:
        f.write(pem)
    os.chmod(path, 0o600)

def save_public_key(key, path: str):
    pem = key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(path, 'wb') as f:
        f.write(pem)

def save_cert(cert, path: str):
    pem = cert.public_bytes(serialization.Encoding.PEM)
    with open(path, 'wb') as f:
        f.write(pem)

def load_private_key(path: str):
    with open(path, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def load_cert(path: str):
    with open(path, 'rb') as f:
        return x509.load_pem_x509_certificate(f.read())

def cmd_init_root(args):
    os.makedirs(args.out_dir, exist_ok=True)
    ca = init_root(args.validity_days)
    
    cert_path = os.path.join(args.out_dir, "root_ca.crt")
    key_path = os.path.join(args.out_dir, "root_ca.key")
    
    save_cert(ca.cert, cert_path)
    save_private_key(ca.private_key, key_path)
    print(f"Root CA initialized at {args.out_dir}")

def cmd_issue_gateway_cert(args):
    os.makedirs(args.out_dir, exist_ok=True)
    ca_cert_path = os.path.join(args.ca_dir, "root_ca.crt")
    ca_key_path = os.path.join(args.ca_dir, "root_ca.key")
    
    if not os.path.exists(ca_cert_path) or not os.path.exists(ca_key_path):
        sys.exit(f"CA not found in {args.ca_dir}")
        
    ca_cert = load_cert(ca_cert_path)
    ca_key = load_private_key(ca_key_path)
    ca = CertificateAuthority(ca_cert, ca_key)
    
    cert, key = issue_leaf_cert(ca, args.agency_id, args.san, args.validity_days)
    
    agency_lower = args.agency_id.lower()
    cert_path = os.path.join(args.out_dir, f"{agency_lower}_gateway.crt")
    key_path = os.path.join(args.out_dir, f"{agency_lower}_gateway.key")
    
    save_cert(cert, cert_path)
    save_private_key(key, key_path)
    print(f"Gateway certificate issued for {args.agency_id} at {args.out_dir}")

def cmd_issue_signing_key(args):
    os.makedirs(args.out_dir, exist_ok=True)
    priv, pub = generate_ml_dsa_keypair()
    
    agency_lower = args.agency_id.lower()
    priv_path = os.path.join(args.out_dir, f"{agency_lower}_ml_dsa65.pem")
    pub_path = os.path.join(args.out_dir, f"{agency_lower}_ml_dsa65.pub")
    
    save_private_key(priv, priv_path)
    save_public_key(pub, pub_path)
    print(f"Signing key issued for {args.agency_id} at {args.out_dir}")

def cmd_export_trust_bundle(args):
    agencies = args.agencies.split(',')
    exporter = TrustBundleExporter()
    
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Simple expiry logic for the bundle if applicable
    expiry_str = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)).isoformat()
    
    for agency in agencies:
        agency_lower = agency.lower()
        gateway_dir = os.path.join(args.pki_root, f"gateway_{agency_lower}")
        
        cert_path = os.path.join(gateway_dir, f"{agency_lower}_gateway.crt")
        pub_path = os.path.join(gateway_dir, f"{agency_lower}_ml_dsa65.pub")
        
        if not os.path.exists(cert_path) or not os.path.exists(pub_path):
            sys.exit(f"Missing artifacts for {agency} in {gateway_dir}")
            
        cert = load_cert(cert_path)
        with open(pub_path, 'rb') as f:
            pub_key = serialization.load_pem_public_key(f.read())
            
        cert_fp = get_cert_fingerprint(cert)
        pub_fp = get_pubkey_fingerprint(pub_key)
        
        # Public key path is relative to the config or standard
        pub_path_rel = f"gateway_{agency_lower}/{agency_lower}_ml_dsa65.pub"
        
        exporter.add(TrustBundleEntry(
            agency_id=agency,
            payload_signing_public_key_path=pub_path_rel,
            payload_signing_public_key_fingerprint=pub_fp,
            tls_certificate_fingerprint=cert_fp,
            issue_timestamp=now_str,
            expiry_timestamp=expiry_str
        ))
        
    exporter.save(args.out)
    print(f"Trust bundle exported to {args.out}")

def cmd_revoke(args):
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        
    rl = RevocationList.load(args.out)
    
    # We need the fingerprint. If the user passes agency, we need to know what fingerprint it is,
    # or the user passes fingerprint? 
    # HLD specifies 'qstie-ca revoke --agency-id RAW --key-type tls_cert --reason "..." --out pki/revocation_list.yaml'
    # Wait, if only agency_id and key_type are provided, how do we get the fingerprint? 
    # Usually you provide the cert to revoke. 
    # Let's add an optional fingerprint arg, or we derive it from pki_root? The prompt example does not specify fingerprint argument, but revocation entry REQUIRES fingerprint.
    # Let's add --fingerprint argument. Wait, prompt says: 
    # qstie-ca revoke --agency-id RAW --key-type tls_cert --reason "suspected key compromise" --out pki/revocation_list.yaml
    # If there's no --fingerprint, where does fingerprint come from? Maybe there is a --fingerprint argument I should add?
    # Or we assume there is a pki_root or we add --fingerprint. I'll add --fingerprint.
    
    fp = getattr(args, 'fingerprint', 'unknown_fingerprint')
    if fp == 'unknown_fingerprint':
        # Let's just make --fingerprint required
        pass

    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rl.add(RevocationEntry(
        fingerprint=args.fingerprint,
        key_type=args.key_type,
        agency_id=args.agency_id,
        reason=args.reason,
        revoked_at=now_str
    ))
    rl.save(args.out)
    print(f"Revoked {args.agency_id} {args.key_type} in {args.out}")

def main():
    parser = argparse.ArgumentParser(prog="qstie-ca")
    subparsers = parser.add_subparsers(required=True)
    
    p_init = subparsers.add_parser("init-root")
    p_init.add_argument("--out-dir", required=True)
    p_init.add_argument("--validity-days", type=int, default=3650)
    p_init.set_defaults(func=cmd_init_root)
    
    p_cert = subparsers.add_parser("issue-gateway-cert")
    p_cert.add_argument("--agency-id", required=True)
    p_cert.add_argument("--ca-dir", required=True)
    p_cert.add_argument("--san", required=True)
    p_cert.add_argument("--validity-days", type=int, default=90)
    p_cert.add_argument("--out-dir", required=True)
    p_cert.set_defaults(func=cmd_issue_gateway_cert)
    
    p_sign = subparsers.add_parser("issue-signing-key")
    p_sign.add_argument("--agency-id", required=True)
    p_sign.add_argument("--out-dir", required=True)
    p_sign.set_defaults(func=cmd_issue_signing_key)
    
    p_trust = subparsers.add_parser("export-trust-bundle")
    p_trust.add_argument("--agencies", required=True)
    p_trust.add_argument("--pki-root", required=True)
    p_trust.add_argument("--out", required=True)
    p_trust.set_defaults(func=cmd_export_trust_bundle)
    
    p_revoke = subparsers.add_parser("revoke")
    p_revoke.add_argument("--agency-id", required=True)
    p_revoke.add_argument("--key-type", required=True)
    p_revoke.add_argument("--reason", required=True)
    p_revoke.add_argument("--out", required=True)
    p_revoke.add_argument("--fingerprint", required=True) # Making it explicit
    p_revoke.set_defaults(func=cmd_revoke)
    
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as e:
        sys.exit(f"Error: {e}")

if __name__ == "__main__":
    main()
