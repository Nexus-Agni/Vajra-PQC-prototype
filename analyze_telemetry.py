import json
import numpy as np
import pandas as pd
from pathlib import Path

def bootstrap_median_ci(data, n_resamples=1000, ci=0.95):
    """Calculate bootstrapped median confidence interval."""
    # Remove NaNs
    data = np.array(data)
    data = data[~np.isnan(data)]
    n = len(data)
    if n == 0:
        return 0.0, 0.0
    
    medians = np.zeros(n_resamples)
    for i in range(n_resamples):
        sample = np.random.choice(data, size=n, replace=True)
        medians[i] = np.median(sample)
        
    alpha = 1.0 - ci
    lower = np.percentile(medians, alpha / 2.0 * 100)
    upper = np.percentile(medians, (1.0 - alpha / 2.0) * 100)
    return lower, upper

def load_jsonl(path):
    data = []
    with open(path, 'r') as f:
        for line in f:
            if not line.strip(): continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return pd.json_normalize(data)

def main():
    import sys
    base_dir_arg = sys.argv[1] if len(sys.argv) > 1 else None
    
    if base_dir_arg:
        base_dir = Path(base_dir_arg)
    else:
        base_dir = Path("stat-data/archive_flawed_phase7")
        if not base_dir.exists():
            base_dir = Path("results/phase5/evidence/archive_flawed_phase7")
    
    file_a = base_dir / "telemetry_a.jsonl"
    file_b = base_dir / "telemetry_b.jsonl"
    
    if not file_a.exists() or not file_b.exists():
        print(f"Error: Could not find telemetry files in {base_dir}")
        return
        
    df_a = load_jsonl(file_a)
    df_b = load_jsonl(file_b)
    
    # Rename columns to remove 'telemetry.' prefix if present
    df_a.columns = [c.replace('telemetry.', '') for c in df_a.columns]
    df_b.columns = [c.replace('telemetry.', '') for c in df_b.columns]
    
    # Group A by transaction_id using earliest/latest timestamps
    agg_a = {
        't_received': 'min',
        't_extracted': 'min',
        't_signed': 'max',
        't_acked': 'max'
    }
    # only aggregate columns that exist
    agg_a = {k: v for k, v in agg_a.items() if k in df_a.columns}
    df_a_grouped = df_a.groupby('transaction_id').agg(agg_a).reset_index()
    
    # Group B by transaction_id using earliest/latest timestamps
    agg_b = {
        't_received_b': 'min',
        't_verified_b': 'min',
        't_ingested_b': 'max'
    }
    agg_b = {k: v for k, v in agg_b.items() if k in df_b.columns}
    df_b_grouped = df_b.groupby('transaction_id').agg(agg_b).reset_index()
    
    # Join A and B
    df_merged = pd.merge(df_a_grouped, df_b_grouped, on='transaction_id', how='inner')
    
    # Decompose Latency
    # Convert ns to ms
    NS_TO_MS = 1e6
    
    # Crypto Overhead: (t_signed - t_extracted) + (t_verified_b - t_received_b)
    crypto_a = (df_merged['t_signed'] - df_merged['t_extracted']) / NS_TO_MS
    crypto_b = (df_merged['t_verified_b'] - df_merged['t_received_b']) / NS_TO_MS
    df_merged['crypto_overhead_ms'] = crypto_a + crypto_b
    
    # Network Transit: (t_received_b - t_signed)
    df_merged['network_transit_ms'] = (df_merged['t_received_b'] - df_merged['t_signed']) / NS_TO_MS
    
    # Filter out potential anomalies where latency < 0
    df_merged = df_merged[(df_merged['crypto_overhead_ms'] > 0) & (df_merged['network_transit_ms'] > 0)]
    
    # Sample N=1000 if there are more
    N = 1000
    if len(df_merged) > N:
        # Sample N events or just take first N? Let's take the first N (e.g. ignoring warmup but we just take N)
        # We can just randomly sample or take head. 
        # I'll just sample 1000 reproducible.
        df_merged = df_merged.sample(n=N, random_state=42)
    elif len(df_merged) > 0:
        pass # use all
    else:
        print("No valid events after merging and filtering.")
        return

    # Calculate Bootstrapped Median CIs
    crypto_median = df_merged['crypto_overhead_ms'].median()
    crypto_lower, crypto_upper = bootstrap_median_ci(df_merged['crypto_overhead_ms'])
    
    network_median = df_merged['network_transit_ms'].median()
    network_lower, network_upper = bootstrap_median_ci(df_merged['network_transit_ms'])
    
    print(f"Summary Statistics (N={len(df_merged)}):")
    print(f"----------------------------------------")
    print(f"Crypto Overhead:")
    print(f"  Median: {crypto_median:.4f} ms")
    print(f"  95% CI: [{crypto_lower:.4f}, {crypto_upper:.4f}] ms")
    print()
    print(f"Network Transit:")
    print(f"  Median: {network_median:.4f} ms")
    print(f"  95% CI: [{network_lower:.4f}, {network_upper:.4f}] ms")

if __name__ == "__main__":
    main()
