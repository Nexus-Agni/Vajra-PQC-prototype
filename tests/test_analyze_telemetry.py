import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze_telemetry import bootstrap_median_ci

def test_bootstrap_median_ci():
    # Simple deterministic check
    data = [10.0] * 100
    lower, upper = bootstrap_median_ci(data, n_resamples=100)
    assert lower == 10.0
    assert upper == 10.0
    
    # Check bounds
    np.random.seed(42)
    data_2 = np.random.normal(50, 10, 1000) # median around 50
    lower_2, upper_2 = bootstrap_median_ci(data_2, n_resamples=200)
    assert 48.0 < lower_2 < 52.0
    assert 48.0 < upper_2 < 52.0

def test_empty_data():
    lower, upper = bootstrap_median_ci([], n_resamples=100)
    assert lower == 0.0
    assert upper == 0.0
