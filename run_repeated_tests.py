import subprocess
import time
import random

def run_campaign():
    runs = 50
    passes = 0
    failures = 0
    
    with open("results/phase1/logs/repeated_validation.log", "w") as log:
        log.write(f"Starting repeated validation campaign: {runs} runs\n")
        
        # We will set a base seed and derive per-run seeds for deterministic randomized testing
        base_seed = 1337
        random.seed(base_seed)
        
        for i in range(runs):
            run_seed = random.randint(1, 1000000)
            start = time.time()
            
            # Use pytest-randomly seed control if available, or pass via environment
            # pytest-randomly reads --randomly-seed
            result = subprocess.run(
                ["pytest", "tests/", "-q", f"--randomly-seed={run_seed}"],
                capture_output=True,
                text=True
            )
            
            duration = time.time() - start
            
            if result.returncode == 0:
                passes += 1
                log.write(f"Run {i+1}/{runs} [Seed: {run_seed}] - PASS ({duration:.2f}s)\n")
            else:
                failures += 1
                log.write(f"Run {i+1}/{runs} [Seed: {run_seed}] - FAIL ({duration:.2f}s)\n")
                log.write(f"Failure Output:\n{result.stdout}\n{result.stderr}\n")
                
        log.write(f"\nCampaign Complete.\n")
        log.write(f"Total Runs: {runs}\n")
        log.write(f"Passes: {passes}\n")
        log.write(f"Failures: {failures}\n")
        
    print(f"Repeated Validation: {passes}/{runs} passed, {failures} failed.")

if __name__ == "__main__":
    run_campaign()
