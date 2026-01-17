"""
Test script for Forecasting module
Verifies that forecasting results are correct
"""

import pandas as pd
from pathlib import Path

def test_forecasting():
    """Test forecasting outputs"""
    print("Testing Forecasting Module Outputs...")
    print("=" * 60)
    
    forecast_path = Path('forecast_results')
    
    # Test 1: Check if output files exist
    print("\n1. Checking output files...")
    required_files = [
        'daily_forecasts.csv',
        'daily_forecasts_summary.csv',
        'state_forecasts.csv',
        'state_forecasts_summary.csv',
        'forecasts_summary.json'
    ]
    
    all_exist = True
    for file in required_files:
        file_path = forecast_path / file
        exists = file_path.exists()
        status = "OK" if exists else "MISSING"
        print(f"   {file}: {status}")
        if not exists:
            all_exist = False
    
    if not all_exist:
        print("\nERROR: Some output files are missing!")
        print("Please run 'python forecasting_models.py' first to generate forecasts.")
        return False
    
    # Test 2: Validate daily forecasts summary
    print("\n2. Validating daily forecasts summary...")
    daily_summary_df = pd.read_csv(forecast_path / 'daily_forecasts_summary.csv')
    print(f"   Number of forecast series: {len(daily_summary_df)}")
    print(f"   Metrics: {', '.join(daily_summary_df['metric'].unique().tolist())}")
    print(f"   Forecast types: {', '.join(daily_summary_df['forecast_type'].unique().tolist())}")
    
    # Check required columns
    required_cols = ['metric', 'forecast_type', 'forecast_periods', 'mae', 'rmse', 'mape', 'model_order']
    missing_cols = [col for col in required_cols if col not in daily_summary_df.columns]
    if missing_cols:
        print(f"   ERROR: Missing columns: {missing_cols}")
        return False
    else:
        print(f"   All required columns present: OK")
    
    # Test 3: Validate state forecasts summary
    print("\n3. Validating state forecasts summary...")
    state_summary_df = pd.read_csv(forecast_path / 'state_forecasts_summary.csv')
    print(f"   Number of state forecasts: {len(state_summary_df)}")
    print(f"   Sample states: {', '.join(state_summary_df['state'].head(5).tolist())}")
    
    # Check required columns
    state_required_cols = ['state', 'forecast_type', 'forecast_periods', 'mae', 'rmse', 'mape', 'model_order']
    missing_cols = [col for col in state_required_cols if col not in state_summary_df.columns]
    if missing_cols:
        print(f"   ERROR: Missing columns: {missing_cols}")
        return False
    else:
        print(f"   All required columns present: OK")
    
    # Test 4: Check data quality
    print("\n4. Checking data quality...")
    
    # Check for NaN values in metrics
    if daily_summary_df[['mae', 'rmse', 'mape']].isnull().any().any():
        print(f"   WARNING: NaN values found in daily forecast metrics")
    else:
        print(f"   No NaN values in daily forecast metrics: OK")
    
    if state_summary_df[['mae', 'rmse', 'mape']].isnull().any().any():
        print(f"   WARNING: NaN values found in state forecast metrics")
    else:
        print(f"   No NaN values in state forecast metrics: OK")
    
    # Check forecast periods are positive
    if (daily_summary_df['forecast_periods'] <= 0).any():
        print(f"   ERROR: Invalid forecast periods found in daily forecasts")
        return False
    else:
        print(f"   All forecast periods are positive: OK")
    
    if (state_summary_df['forecast_periods'] <= 0).any():
        print(f"   ERROR: Invalid forecast periods found in state forecasts")
        return False
    else:
        print(f"   All forecast periods are positive: OK")
    
    # Test 5: Validate detailed forecasts
    print("\n5. Validating detailed forecast files...")
    
    daily_forecasts_df = pd.read_csv(forecast_path / 'daily_forecasts.csv')
    print(f"   Daily forecasts: {len(daily_forecasts_df)} rows")
    print(f"   Unique metrics: {daily_forecasts_df['metric'].nunique()}")
    print(f"   Unique forecast types: {daily_forecasts_df['forecast_type'].nunique()}")
    
    state_forecasts_df = pd.read_csv(forecast_path / 'state_forecasts.csv')
    print(f"   State forecasts: {len(state_forecasts_df)} rows")
    print(f"   Unique states: {state_forecasts_df['state'].nunique()}")
    
    # Test 6: Display sample results
    print("\n6. Sample Results:")
    print("\n   Daily Forecasts Summary (Top 3 by forecast_periods):")
    top_daily = daily_summary_df.nlargest(3, 'forecast_periods')[['metric', 'forecast_type', 'forecast_periods', 'mae', 'rmse', 'mape']]
    print(top_daily.to_string(index=False))
    
    print("\n   State Forecasts Summary (Top 3 by forecast_periods):")
    top_state = state_summary_df.nlargest(3, 'forecast_periods')[['state', 'forecast_type', 'forecast_periods', 'mae', 'rmse', 'mape']]
    print(top_state.to_string(index=False))
    
    print("\n" + "=" * 60)
    print("SUCCESS: Forecasting module outputs are valid!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_forecasting()
