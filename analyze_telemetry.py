import json
import os
import re
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def bootstrap_median_ci_cluster(df, col, cluster_col='iteration', n_resamples=1000, ci=0.95):
    """
    Cluster bootstrapping to account for non-independent events within the same iteration (queueing correlation).
    Resamples iterations with replacement, rather than individual events.
    """
    clusters = df[cluster_col].unique()
    n_clusters = len(clusters)
    if n_clusters == 0: return 0.0, 0.0
    
    medians = np.zeros(n_resamples)
    for i in range(n_resamples):
        # Sample cluster IDs with replacement
        sampled_clusters = np.random.choice(clusters, size=n_clusters, replace=True)
        # Reconstruct the dataset from the sampled clusters
        sampled_df = pd.concat([df[df[cluster_col] == c] for c in sampled_clusters])
        medians[i] = sampled_df[col].median()
        
    alpha = 1.0 - ci
    lower = np.percentile(medians, alpha / 2.0 * 100)
    upper = np.percentile(medians, (1.0 - alpha / 2.0) * 100)
    return lower, upper

def load_jsonl(path):
    data = []
    with open(path, 'r') as f:
        for line in f:
            if not line.strip(): continue
            try: data.append(json.loads(line))
            except: continue
    if not data: return pd.DataFrame()
    return pd.json_normalize(data)

def plot_component_boxplots(df, output_dir):
    labels = df['label'].unique().tolist()
    labels.sort()
    data_crypto = [df[df['label'] == l]['crypto_path_ms'].dropna() for l in labels]
    data_network = [df[df['label'] == l]['network_transit_ms'].dropna() for l in labels]
    fig, ax = plt.subplots(figsize=(14, 8))
    pos_c = np.arange(len(labels)) * 2.0 - 0.4
    pos_n = np.arange(len(labels)) * 2.0 + 0.4
    ax.boxplot(data_crypto, positions=pos_c, widths=0.6, patch_artist=True, boxprops=dict(facecolor="lightblue"))
    ax.boxplot(data_network, positions=pos_n, widths=0.6, patch_artist=True, boxprops=dict(facecolor="lightgreen"))
    ax.set_xticks(np.arange(len(labels)) * 2.0)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='lightblue', label='Crypto-Path Latency'), Patch(facecolor='lightgreen', label='Network Transit')]
    ax.legend(handles=legend_elements, loc='upper right')
    ax.set_title("Component Latency: Crypto-Path vs Network Transit")
    ax.set_ylabel("Latency (ms) - Log Scale")
    ax.set_yscale("log")
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "boxplot_components.png"), dpi=300)
    plt.close(fig)

def plot_cdf_overlay(df, col, title, filename, output_dir):
    labels = df['label'].unique().tolist()
    labels.sort()
    colors = plt.get_cmap("tab10").colors
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, label in enumerate(labels):
        data = df[df['label'] == label][col].dropna()
        if len(data) == 0: continue
        x = data.sort_values()
        y = pd.Series(1, index=x.index).cumsum() / len(x)
        ax.plot(x, y, label=label, color=colors[i % len(colors)])
    ax.set_title(title)
    ax.set_xlabel(f"{title} (ms) - Log Scale")
    ax.set_ylabel("CDF")
    ax.set_xscale("log")
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close(fig)

def main():
    raw_dir = Path("stat-data/phase7/raw")
    output_dir = Path("stat-data/phase7")
    if not raw_dir.exists(): return
    pattern = re.compile(r"telemetry_a_(.*)_(.*)_iter(\d+)\.jsonl")
    configs = {}
    for file_path in raw_dir.glob("telemetry_a_*.jsonl"):
        match = pattern.search(file_path.name)
        if match:
            crypto, profile, iteration = match.groups()
            key = (crypto, profile)
            if key not in configs: configs[key] = []
            configs[key].append(iteration)

    all_data = []
    summary_results = []
    NS_TO_MS = 1e6

    for (crypto, profile), iterations in configs.items():
        iter_merged_list = []
        for it in iterations:
            f_a = raw_dir / f"telemetry_a_{crypto}_{profile}_iter{it}.jsonl"
            f_b = raw_dir / f"telemetry_b_{crypto}_{profile}_iter{it}.jsonl"
            if not (f_a.exists() and f_b.exists()): continue
            df_a = load_jsonl(f_a)
            df_b = load_jsonl(f_b)
            if df_a.empty or df_b.empty: continue
            
            df_a.columns = [c.replace('telemetry.', '') for c in df_a.columns]
            df_b.columns = [c.replace('telemetry.', '') for c in df_b.columns]
            
            # Using max for extraction/signing to isolate the final successful attempt. E2E uses min for received.
            agg_a = {k: v for k, v in {'t_received': 'min', 't_extracted': 'max', 't_signed': 'max', 't_acked': 'max'}.items() if k in df_a.columns}
            df_a_grouped = df_a.groupby('transaction_id').agg(agg_a).reset_index()
            
            agg_b = {k: v for k, v in {'t_received_b': 'max', 't_verified_b': 'max', 't_ingested_b': 'max'}.items() if k in df_b.columns}
            df_b_grouped = df_b.groupby('transaction_id').agg(agg_b).reset_index()
            
            df_merged = pd.merge(df_a_grouped, df_b_grouped, on='transaction_id', how='inner')
            
            # Enforce 1000 events per iteration
            if 't_received' in df_merged.columns:
                df_merged = df_merged.sort_values('t_received')
            discard = 1000
            if len(df_merged) >= discard + 1000:
                df_merged = df_merged.iloc[discard:discard+1000]
            elif len(df_merged) > 1000:
                df_merged = df_merged.iloc[-1000:]
                
            df_merged['iteration'] = it
            iter_merged_list.append(df_merged)
            
        if not iter_merged_list: continue
        
        df_combined = pd.concat(iter_merged_list, ignore_index=True)
        
        # Exact definitions
        crypto_a = (df_combined['t_signed'] - df_combined['t_extracted']) / NS_TO_MS
        crypto_b = (df_combined['t_verified_b'] - df_combined['t_received_b']) / NS_TO_MS
        df_combined['crypto_path_ms'] = crypto_a + crypto_b
        df_combined['network_transit_ms'] = (df_combined['t_received_b'] - df_combined['t_signed']) / NS_TO_MS
        df_combined['end_to_end_ms'] = (df_combined['t_ingested_b'] - df_combined['t_received']) / NS_TO_MS
        
        df_combined = df_combined[(df_combined['crypto_path_ms'] > 0) & (df_combined['network_transit_ms'] > 0)]
        if len(df_combined) == 0: continue
            
        df_combined['label'] = f"{crypto}_{profile}"
        all_data.append(df_combined[['label', 'iteration', 'crypto_path_ms', 'network_transit_ms', 'end_to_end_ms']])
        
        c_med = df_combined['crypto_path_ms'].median()
        c_low, c_up = bootstrap_median_ci_cluster(df_combined, 'crypto_path_ms')
        n_med = df_combined['network_transit_ms'].median()
        n_low, n_up = bootstrap_median_ci_cluster(df_combined, 'network_transit_ms')
        e_med = df_combined['end_to_end_ms'].median()
        e_low, e_up = bootstrap_median_ci_cluster(df_combined, 'end_to_end_ms')
        
        summary_results.append({
            "crypto": crypto,
            "profile": profile,
            "count": len(df_combined),
            "crypto_path_median_ms": c_med,
            "crypto_path_ci_95_lower": c_low,
            "crypto_path_ci_95_upper": c_up,
            "network_median_ms": n_med,
            "network_ci_95_lower": n_low,
            "network_ci_95_upper": n_up,
            "end_to_end_median_ms": e_med,
            "end_to_end_ci_95_lower": e_low,
            "end_to_end_ci_95_upper": e_up,
        })
        
    if summary_results:
        pd.DataFrame(summary_results).to_csv(output_dir / "final_decomposed_statistics.csv", index=False)
        full_df = pd.concat(all_data, ignore_index=True)
        plot_cdf_overlay(full_df, 'end_to_end_ms', 'End-to-End Latency', 'cdf_overlay_end_to_end.png', output_dir)
        plot_cdf_overlay(full_df, 'crypto_path_ms', 'Crypto-Path Latency', 'cdf_overlay_crypto.png', output_dir)
        plot_cdf_overlay(full_df, 'network_transit_ms', 'Network Transit', 'cdf_overlay_network.png', output_dir)
        plot_component_boxplots(full_df, output_dir)

if __name__ == "__main__":
    main()
