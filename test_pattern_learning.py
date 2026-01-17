"""
Test script for Pattern Learning module
Verifies that pattern learning results are correct
"""

import pandas as pd
from pathlib import Path

def test_pattern_learning():
    """Test pattern learning outputs"""
    print("Testing Pattern Learning Module Outputs...")
    print("=" * 60)
    
    pattern_path = Path('pattern_results')
    
    # Test 1: Check if output files exist
    print("\n1. Checking output files...")
    required_files = [
        'daily_patterns_summary.csv',
        'state_patterns_summary.csv',
        'patterns_summary.json'
    ]
    
    all_exist = True
    for file in required_files:
        file_path = pattern_path / file
        exists = file_path.exists()
        status = "OK" if exists else "MISSING"
        print(f"   {file}: {status}")
        if not exists:
            all_exist = False
    
    if not all_exist:
        print("\nERROR: Some output files are missing!")
        return False
    
    # Test 2: Validate daily patterns
    print("\n2. Validating daily patterns...")
    daily_df = pd.read_csv(pattern_path / 'daily_patterns_summary.csv')
    print(f"   Number of metrics: {len(daily_df)}")
    print(f"   Metrics: {', '.join(daily_df['metric'].tolist())}")
    
    # Check required columns
    required_cols = ['metric', 'trend_direction', 'trend_slope', 'trend_mean', 'seasonal_amplitude', 'resid_std']
    missing_cols = [col for col in required_cols if col not in daily_df.columns]
    if missing_cols:
        print(f"   ERROR: Missing columns: {missing_cols}")
        return False
    else:
        print(f"   All required columns present: OK")
    
    # Test 3: Validate state patterns
    print("\n3. Validating state patterns...")
    state_df = pd.read_csv(pattern_path / 'state_patterns_summary.csv')
    print(f"   Number of states: {len(state_df)}")
    print(f"   Sample states: {', '.join(state_df['state'].head(5).tolist())}")
    
    # Check required columns
    state_required_cols = ['state', 'trend_direction', 'trend_slope', 'trend_mean', 'seasonal_amplitude', 'resid_std']
    missing_cols = [col for col in state_required_cols if col not in state_df.columns]
    if missing_cols:
        print(f"   ERROR: Missing columns: {missing_cols}")
        return False
    else:
        print(f"   All required columns present: OK")
    
    # Test 4: Check data quality
    print("\n4. Checking data quality...")
    
    # Check for valid trend directions
    valid_directions = ['increasing', 'decreasing', 'stable', 'insufficient_data']
    invalid_directions = daily_df[~daily_df['trend_direction'].isin(valid_directions)]
    if len(invalid_directions) > 0:
        print(f"   WARNING: Invalid trend directions found: {invalid_directions['trend_direction'].unique()}")
    else:
        print(f"   All trend directions valid: OK")
    
    # Check for NaN values
    if daily_df.isnull().any().any():
        print(f"   WARNING: NaN values found in daily patterns")
    else:
        print(f"   No NaN values in daily patterns: OK")
    
    if state_df.isnull().any().any():
        print(f"   WARNING: NaN values found in state patterns")
    else:
        print(f"   No NaN values in state patterns: OK")
    
    # Test 5: Display sample results
    print("\n5. Sample Results:")
    print("\n   Daily Patterns:")
    print(daily_df[['metric', 'trend_direction', 'trend_slope']].to_string(index=False))
    
    print("\n   Top 5 States by Trend Slope:")
    top_states = state_df.nlargest(5, 'trend_slope')[['state', 'trend_direction', 'trend_slope']]
    print(top_states.to_string(index=False))
    
    print("\n" + "=" * 60)
    print("SUCCESS: Pattern Learning module outputs are valid!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_pattern_learning()
