import os
import time
import json
import subprocess
import pandas as pd
import matplotlib.pyplot as plt

EVIDENCE_DIR = '/app/results/phase5/evidence'
os.makedirs(EVIDENCE_DIR, exist_ok=True)

TELEMETRY_A = '/app/results/phase5/evidence/telemetry_a.jsonl'
TELEMETRY_B = '/app/results/phase5/evidence/telemetry_b.jsonl'

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr).strip()

def get_container_name(service_name):
    cmd = f"docker ps --filter name={service_name} --format '{{{{.Names}}}}' | head -n 1"
    res = run_cmd(cmd)
    if not res:
        print(f"Warning: Could not find container for {service_name}")
        return service_name
    return res

def toggle_profile(profile):
    router = get_container_name("netem-router")
    if profile == "adverse":
        cmd_eth0 = f"docker exec {router} bash -c \"tc qdisc add dev eth0 root netem delay 25ms loss 1.5% 2>/dev/null || tc qdisc change dev eth0 root netem delay 25ms loss 1.5%\""
        cmd_eth1 = f"docker exec {router} bash -c \"tc qdisc add dev eth1 root netem delay 25ms loss 1.5% 2>/dev/null || tc qdisc change dev eth1 root netem delay 25ms loss 1.5%\""
        run_cmd(cmd_eth0)
        run_cmd(cmd_eth1)
    else:
        cmd_eth0 = f"docker exec {router} bash -c \"tc qdisc del dev eth0 root 2>/dev/null || true\""
        cmd_eth1 = f"docker exec {router} bash -c \"tc qdisc del dev eth1 root 2>/dev/null || true\""
        run_cmd(cmd_eth0)
        run_cmd(cmd_eth1)

def run_ping():
    gw = get_container_name("gateway-a")
    out = run_cmd(f"docker exec {gw} ping -c 5 172.26.0.2")
    # try to parse average rtt
    avg = 0.0
    for line in out.splitlines():
        if "rtt min/avg/max/mdev" in line:
            parts = line.split("=")[1].strip().split("/")
            avg = float(parts[1])
    return avg

def inject_events(count):
    misp = get_container_name("misp-1")
    if not misp or misp == "misp-1":
        misp = get_container_name("misp")
    run_cmd(f"docker exec {misp} python3 /tmp/misp_publisher_mock.py {count} green")

def main():
    print("Starting Benchmark...")
def main():
    print("Starting Benchmark...")
    results = []

    for crypto in ["X25519", "X25519MLKEM768"]:
        print(f"Setting crypto to {crypto}...")
        os.environ["HYBRID_GROUP"] = crypto
        run_cmd("docker compose -f /app/compose.yaml up -d --force-recreate gateway-a gateway-b")
        time.sleep(10)
    
        for profile in ["stable", "adverse"]:
            print(f"Setting profile {profile} for crypto {crypto}...")
            toggle_profile(profile)
            time.sleep(2)
            
            avg_rtt = run_ping()
            print(f"Actual Ping RTT for {profile} ({crypto}): {avg_rtt}ms")
            
            # Clear telemetry files
            if os.path.exists(TELEMETRY_A): os.remove(TELEMETRY_A)
            if os.path.exists(TELEMETRY_B): os.remove(TELEMETRY_B)
            
            print("Injecting 50 events...")
            inject_events(50)
            
            print("Waiting for events to propagate (30s)...")
            time.sleep(30)
            
            # Parse telemetry
            a_events = []
            if os.path.exists(TELEMETRY_A):
                with open(TELEMETRY_A, 'r') as f:
                    for line in f:
                        try:
                            a_events.append(json.loads(line))
                        except:
                            pass
            
            b_events = []
            if os.path.exists(TELEMETRY_B):
                with open(TELEMETRY_B, 'r') as f:
                    for line in f:
                        try:
                            b_events.append(json.loads(line))
                        except:
                            pass
            
            # Process and align by transaction_id
            df_a = pd.DataFrame([{"tx_id": e["transaction_id"], **e["telemetry"]} for e in a_events if e["state"] == "ACKED"])
            df_b = pd.DataFrame([{"tx_id": e["transaction_id"], **e["telemetry"]} for e in b_events if e["state"] == "ACKED"])
            
            if len(df_a) == 0 or len(df_b) == 0:
                print(f"No completed transactions for {profile} ({crypto})")
                continue
                
            # Merge
            df = pd.merge(df_a, df_b, on="tx_id")
            
            # Calculate latencies
            df['total_latency_ms'] = (df['t_ingested_b'] - df['t_received']) / 1e6
            df['extraction_ms'] = (df['t_extracted'] - df['t_received']) / 1e6
            df['signing_ms'] = (df['t_signed'] - df['t_extracted']) / 1e6
            df['network_and_verify_ms'] = (df['t_verified_b'] - df['t_signed']) / 1e6
            
            mean_latency = df['total_latency_ms'].mean()
            p95_latency = df['total_latency_ms'].quantile(0.95)
            p99_latency = df['total_latency_ms'].quantile(0.99)
            mean_retries = df['retry_count'].mean() if 'retry_count' in df else 0.0
            
            print(f"Metrics for {profile} ({crypto}): Mean={mean_latency:.2f}ms, P95={p95_latency:.2f}ms, Retries={mean_retries:.2f}")
            
            res = {
                "crypto": crypto,
                "profile": profile,
                "avg_rtt_ms": avg_rtt,
                "mean_latency_ms": mean_latency,
                "p95_latency_ms": p95_latency,
                "p99_latency_ms": p99_latency,
                "mean_retries": mean_retries,
                "count": len(df)
            }
            results.append(res)
            
            # Plot CDF of latency
            plt.figure()
            df['total_latency_ms'].hist(cumulative=True, density=1, bins=50)
            plt.title(f"CDF of End-to-End Latency ({crypto} - {profile})")
            plt.xlabel("Latency (ms)")
            plt.ylabel("CDF")
            plt.savefig(f"{EVIDENCE_DIR}/latency_cdf_{crypto}_{profile}.png")
            plt.close()
        
    # Write final report
    final_df = pd.DataFrame(results)
    final_df.to_csv(f"{EVIDENCE_DIR}/benchmark_report.csv", index=False)
    
    # Generate bar chart
    plt.figure(figsize=(10, 6))
    final_df['label'] = final_df['crypto'] + '_' + final_df['profile']
    final_df.plot(x='label', y=['mean_latency_ms', 'p95_latency_ms'], kind='bar')
    plt.title("Latency by Crypto and Network Profile")
    plt.ylabel("Latency (ms)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{EVIDENCE_DIR}/latency_summary.png")
    
    print(f"Benchmark complete. Reports saved to {EVIDENCE_DIR}")

if __name__ == "__main__":
    main()
