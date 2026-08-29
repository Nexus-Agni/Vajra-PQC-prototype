import subprocess
import json
import os
from datetime import datetime

def run_integration_test(run_number):
    print(f"--- Starting Run {run_number} ---")
    
    # Clean up first
    subprocess.run(["docker", "compose", "down", "-v"], check=False)
    
    # Build/Verify environment (already built but ensuring it's up)
    # Start Gateway B
    subprocess.run(["docker", "compose", "up", "-d", "gateway-b"], check=True)
    
    # Execute Phase 4 validation suite
    cmd = [
        "docker", "compose", "run", "--rm", 
        "-e", "GATEWAY_B_HOST=gateway-b", 
        "-e", "GATEWAY_B_PORT=8443", 
        "gateway-a-test", 
        "tests/phase4/test_4_12_15_integration.py", 
        "-v", "-s"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Stop/Reset
    subprocess.run(["docker", "compose", "down", "-v"], check=True)
    
    if result.returncode == 0:
        print(f"Run {run_number} PASS")
        return {"run": run_number, "status": "PASS", "details": "Integration tests passed"}
    else:
        print(f"Run {run_number} FAIL")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return {"run": run_number, "status": "FAIL", "details": result.stdout[-500:]}

def main():
    print("Starting independent repeated validation (5 runs)...")
    results = []
    
    # Get image info
    # Just capturing standard reproducibility info
    import platform
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    
    for i in range(1, 6):
        res = run_integration_test(i)
        results.append(res)
        
    overall = "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL"
    
    evidence = {
        "phase": 4,
        "repetitions": 5,
        "results": results,
        "overall": overall,
        "timestamp": datetime.utcnow().isoformat(),
        "commit": commit,
        "environment": "docker-compose independent runs"
    }
    
    os.makedirs("results/phase4/evidence", exist_ok=True)
    with open("results/phase4/evidence/repeated_validation.json", "w") as f:
        json.dump(evidence, f, indent=2)
        
    print(f"Done. Overall status: {overall}")
    if overall != "PASS":
        exit(1)

if __name__ == "__main__":
    main()
