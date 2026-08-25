import json
import subprocess
import datetime
import os

def run(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout.strip() if res.returncode == 0 else 'NOT_AVAILABLE'
    except Exception:
        return 'NOT_AVAILABLE'

meta = {
    'git_commit': run('git rev-parse HEAD'),
    'git_branch': run('git rev-parse --abbrev-ref HEAD'),
    'git_status': "clean" if not run('git status --porcelain') else "dirty",
    'docker_version': run('docker --version'),
    'compose_version': run('docker compose version'),
    'image_name': 'gateway_b',
    'image_tag': 'latest',
    'image_id': run('docker images -q gateway_b:latest'),
    'image_digest': run('docker inspect --format="{{index .RepoDigests 0}}" gateway_b:latest'),
    'container_id': 'NOT_AVAILABLE',
    'python_version': run('docker run --rm gateway_b python --version'),
    'openssl_version': run('docker run --rm gateway_b python -c "import ssl; print(ssl.OPENSSL_VERSION)"'),
    'operating_system': run('docker run --rm gateway_b uname -a'),
    'test_timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()
}

if not meta['image_digest'] or 'index out of range' in meta['image_digest'] or meta['image_digest'] == 'NOT_AVAILABLE':
    meta['image_digest'] = 'NOT_AVAILABLE (Image only exists locally, no repo digest)'

os.makedirs('results/phase3/evidence', exist_ok=True)
with open('results/phase3/evidence/reproducibility.json', 'w') as f:
    json.dump(meta, f, indent=2)
print("Metadata generated")
