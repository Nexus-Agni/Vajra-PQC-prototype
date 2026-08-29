import sys
import subprocess

def run_cmd(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        pass # Ignore errors from tc qdisc del when they don't exist

def toggle_profile(profile):
    if profile not in ["stable", "adverse"]:
        print("Error: Profile must be 'stable' or 'adverse'.")
        sys.exit(1)
        
    print(f"Switching netem-router to profile: {profile}")
    
    if profile == "adverse":
        cmd_eth0 = "docker compose exec netem-router bash -c \"tc qdisc add dev eth0 root netem delay 50ms 10ms loss 5% 2>/dev/null || tc qdisc change dev eth0 root netem delay 50ms 10ms loss 5%\""
        cmd_eth1 = "docker compose exec netem-router bash -c \"tc qdisc add dev eth1 root netem delay 50ms 10ms loss 5% 2>/dev/null || tc qdisc change dev eth1 root netem delay 50ms 10ms loss 5%\""
        run_cmd(cmd_eth0)
        run_cmd(cmd_eth1)
        print("SUCCESS: Adverse network conditions applied (50ms latency, 5% packet loss).")
    else:
        cmd_eth0 = "docker compose exec netem-router bash -c \"tc qdisc del dev eth0 root 2>/dev/null || true\""
        cmd_eth1 = "docker compose exec netem-router bash -c \"tc qdisc del dev eth1 root 2>/dev/null || true\""
        run_cmd(cmd_eth0)
        run_cmd(cmd_eth1)
        print("SUCCESS: Stable network conditions applied (no tc rules).")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} [stable|adverse]")
        sys.exit(1)
    
    toggle_profile(sys.argv[1])
