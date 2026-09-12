import pandas as pd; df=pd.read_json('stat-data/phase7/raw/telemetry_a_X25519_stable_iter2.jsonl', lines=True); print(df['telemetry.retry_count'].value_counts())
