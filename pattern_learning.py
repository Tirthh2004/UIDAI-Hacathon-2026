"""
Pattern Learning Module - STL Decomposition
AI-Driven Early Warning System for Aadhaar Update Surges

This module implements seasonal pattern learning using STL (Seasonal and Trend using Loess) decomposition
to model normal behavior and learn historical trends/seasonal patterns.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.tsa.seasonal import STL
import warnings
import json
from datetime import datetime
warnings.filterwarnings('ignore')


class PatternLearner:
    """
    Learn and extract patterns from time-series data using STL decomposition
    
    Capability: Pattern Learning
    Algorithm: STL Decomposition
    """
    
    def __init__(self, data_path='processed_data', output_path='pattern_results'):
        """
        Initialize the Pattern Learner
        
        Args:
            data_path: Path to processed data directory
            output_path: Path to save pattern learning results
        """
        self.data_path = Path(data_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(exist_ok=True)
        
        # Storage for patterns
        self.patterns = {}
        
    def load_data(self):
        """Load cleaned data files"""
        print("Loading cleaned data...")
        try:
            self.biometric_df = pd.read_csv(
                self.data_path / 'biometric_cleaned.csv',
                parse_dates=['date']
            )
            self.demographic_df = pd.read_csv(
                self.data_path / 'demographic_cleaned.csv',
                parse_dates=['date']
            )
            self.enrolment_df = pd.read_csv(
                self.data_path / 'enrolment_cleaned.csv',
                parse_dates=['date']
            )
            
            # Ensure date columns are datetime
            for df in [self.biometric_df, self.demographic_df, self.enrolment_df]:
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
            
            print(f"  Biometric: {len(self.biometric_df):,} rows")
            print(f"  Demographic: {len(self.demographic_df):,} rows")
            print(f"  Enrolment: {len(self.enrolment_df):,} rows")
            
            return True
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return False
    
    def prepare_time_series(self, df, group_cols, value_col, freq='D'):
        """
        Prepare time series data for decomposition
        
        Args:
            df: DataFrame with data
            group_cols: Columns to group by (e.g., ['state'], ['state', 'district'])
            value_col: Column with values to aggregate
            freq: Frequency for time series ('D' for daily, 'W' for weekly, 'M' for monthly)
        
        Returns:
            Dictionary of time series (one per group)
        """
        time_series_dict = {}
        
        # Group and aggregate
        grouped = df.groupby(group_cols + ['date'])[value_col].sum().reset_index()
        
        # Create date range
        min_date = grouped['date'].min()
        max_date = grouped['date'].max()
        date_range = pd.date_range(start=min_date, end=max_date, freq=freq)
        
        # Get unique groups
        if len(group_cols) == 1:
            groups = grouped[group_cols[0]].unique()
            for group in groups:
                group_data = grouped[grouped[group_cols[0]] == group].copy()
                group_data = group_data.set_index('date')[value_col]
                
                # Reindex to full date range and fill missing with 0
                group_ts = group_data.reindex(date_range, fill_value=0)
                
                # Remove all-zero series
                if group_ts.sum() > 0:
                    time_series_dict[group] = group_ts
        
        elif len(group_cols) == 2:
            # For state-district combinations
            groups = grouped.groupby(group_cols).size().reset_index()
            for _, row in groups.iterrows():
                key = f"{row[group_cols[0]]}_{row[group_cols[1]]}"
                group_data = grouped[
                    (grouped[group_cols[0]] == row[group_cols[0]]) &
                    (grouped[group_cols[1]] == row[group_cols[1]])
                ].copy()
                group_data = group_data.set_index('date')[value_col]
                group_ts = group_data.reindex(date_range, fill_value=0)
                if group_ts.sum() > 0:
                    time_series_dict[key] = group_ts
        
        return time_series_dict, date_range
    
    def stl_decompose(self, ts, seasonal_period=None, robust=True):
        """
        Perform STL decomposition on a time series
        
        Args:
            ts: Pandas Series with datetime index
            seasonal_period: Seasonal period (auto-detect if None)
            robust: Use robust decomposition (handles outliers)
        
        Returns:
            STL decomposition object with trend, seasonal, resid components
        """
        # Auto-detect seasonal period if not provided
        if seasonal_period is None:
            # Default to weekly seasonality for daily data
            if len(ts) > 14:
                seasonal_period = 7  # Weekly
            else:
                seasonal_period = max(3, len(ts) // 2)
        
        # Ensure seasonal period is odd (STL requirement)
        if seasonal_period % 2 == 0:
            seasonal_period += 1
        
        # Minimum data requirement
        if len(ts) < seasonal_period * 2:
            return None
        
        try:
            # Perform STL decomposition
            stl = STL(ts, seasonal=seasonal_period, robust=robust)
            result = stl.fit()
            return result
        except Exception as e:
            print(f"  Warning: STL decomposition failed: {str(e)}")
            return None
    
    def extract_patterns(self, stl_result, ts_name):
        """
        Extract patterns from STL decomposition
        
        Args:
            stl_result: STL decomposition result
            ts_name: Name identifier for the time series
        
        Returns:
            Dictionary with extracted patterns
        """
        if stl_result is None:
            return None
        
        patterns = {
            'name': ts_name,
            'trend': stl_result.trend.values.tolist(),
            'seasonal': stl_result.seasonal.values.tolist(),
            'resid': stl_result.resid.values.tolist(),
            'observed': stl_result.observed.values.tolist()
        }
        
        # Calculate pattern statistics
        patterns['trend_mean'] = float(stl_result.trend.mean())
        patterns['trend_slope'] = float(np.polyfit(range(len(stl_result.trend)), stl_result.trend.values, 1)[0])
        patterns['seasonal_amplitude'] = float(stl_result.seasonal.std())
        patterns['resid_std'] = float(stl_result.resid.std())
        
        # Trend direction
        if patterns['trend_slope'] > 0:
            patterns['trend_direction'] = 'increasing'
        elif patterns['trend_slope'] < 0:
            patterns['trend_direction'] = 'decreasing'
        else:
            patterns['trend_direction'] = 'stable'
        
        return patterns
    
    def learn_state_level_patterns(self):
        """Learn patterns at state level"""
        print(f"\n{'='*80}")
        print("Learning State-Level Patterns")
        print(f"{'='*80}")
        
        # Prepare time series for biometric data
        print("\n1. Biometric Updates - State Level")
        bio_state_ts, date_range = self.prepare_time_series(
            self.biometric_df,
            group_cols=['state'],
            value_col='bio_age_5_17'
        )
        
        # Also aggregate total biometric
        bio_total = self.biometric_df.copy()
        bio_total['bio_total'] = bio_total['bio_age_5_17'] + bio_total['bio_age_17_']
        bio_total_ts, _ = self.prepare_time_series(
            bio_total,
            group_cols=['state'],
            value_col='bio_total'
        )
        
        state_patterns = {}
        
        # Process each state
        states_to_process = list(bio_total_ts.keys())
        print(f"  Processing {len(states_to_process)} states...")
        
        for state in states_to_process:
            if state in bio_total_ts:
                ts = bio_total_ts[state]
                
                # Perform STL decomposition
                print(f"  Processing: {state}")
                stl_result = self.stl_decompose(ts, seasonal_period=7, robust=True)
                
                if stl_result is not None:
                    patterns = self.extract_patterns(stl_result, state)
                    if patterns:
                        state_patterns[state] = patterns
        
        self.patterns['state_biometric'] = state_patterns
        print(f"  Completed: {len(state_patterns)} states")
        
        return state_patterns
    
    def learn_daily_aggregated_patterns(self):
        """Learn patterns from daily aggregated data"""
        print(f"\n{'='*80}")
        print("Learning Daily Aggregated Patterns")
        print(f"{'='*80}")
        
        # Load daily aggregated data if available
        daily_path = Path('analysis_results') / 'daily_aggregated_data.csv'
        if daily_path.exists():
            daily_df = pd.read_csv(daily_path, parse_dates=['date'])
        else:
            print("  Daily aggregated data not found. Creating from raw data...")
            # Create daily aggregation
            bio_daily = self.biometric_df.groupby('date').agg({
                'bio_age_5_17': 'sum',
                'bio_age_17_': 'sum'
            }).reset_index()
            bio_daily['bio_total'] = bio_daily['bio_age_5_17'] + bio_daily['bio_age_17_']
            
            demo_daily = self.demographic_df.groupby('date').agg({
                'demo_age_5_17': 'sum',
                'demo_age_17_': 'sum'
            }).reset_index()
            demo_daily['demo_total'] = demo_daily['demo_age_5_17'] + demo_daily['demo_age_17_']
            
            enrol_daily = self.enrolment_df.groupby('date').agg({
                'age_0_5': 'sum',
                'age_5_17': 'sum',
                'age_18_greater': 'sum'
            }).reset_index()
            enrol_daily['enrol_total'] = enrol_daily['age_0_5'] + enrol_daily['age_5_17'] + enrol_daily['age_18_greater']
            
            daily_df = bio_daily.merge(demo_daily, on='date', how='outer').merge(enrol_daily, on='date', how='outer')
            daily_df = daily_df.sort_values('date').fillna(0)
        
        daily_patterns = {}
        
        # Process each metric
        metrics = ['bio_total', 'demo_total', 'enrol_total']
        
        for metric in metrics:
            if metric in daily_df.columns:
                print(f"\n2. Processing: {metric}")
                
                # Create time series - use all data, fill zeros with forward fill
                ts_data = daily_df.set_index('date')[metric].sort_index()
                
                # For sparse data, fill zeros with small value or forward fill
                # But keep original for STL (STL can handle zeros if robust=True)
                ts_data_clean = ts_data.copy()
                
                # Check if data is too sparse
                non_zero_ratio = (ts_data_clean > 0).sum() / len(ts_data_clean)
                
                if non_zero_ratio < 0.3:  # If less than 30% non-zero, data is too sparse
                    print(f"  Warning: Data too sparse ({non_zero_ratio*100:.1f}% non-zero). Skipping STL decomposition.")
                    # Still calculate basic statistics
                    patterns = {
                        'name': metric,
                        'trend_direction': 'insufficient_data',
                        'trend_slope': 0.0,
                        'trend_mean': float(ts_data_clean.mean()),
                        'seasonal_amplitude': 0.0,
                        'resid_std': float(ts_data_clean.std())
                    }
                    daily_patterns[metric] = patterns
                    continue
                
                if len(ts_data_clean) > 21:  # Minimum data requirement (3 weeks)
                    # Use weekly aggregation for sparse daily data
                    if non_zero_ratio < 0.5:
                        print(f"  Data sparse. Aggregating to weekly frequency...")
                        ts_data_clean = ts_data_clean.resample('W').sum()
                        seasonal_period = 4  # 4 weeks for monthly pattern
                    else:
                        seasonal_period = 7  # Weekly pattern for daily data
                    
                    # Perform STL decomposition
                    stl_result = self.stl_decompose(ts_data_clean, seasonal_period=seasonal_period, robust=True)
                    
                    if stl_result is not None:
                        patterns = self.extract_patterns(stl_result, metric)
                        if patterns:
                            daily_patterns[metric] = patterns
                            print(f"  Trend direction: {patterns['trend_direction']}")
                            print(f"  Trend slope: {patterns['trend_slope']:.2f}")
                            print(f"  Seasonal amplitude: {patterns['seasonal_amplitude']:.2f}")
                    else:
                        # Fallback: calculate simple trend
                        print(f"  STL failed. Using simple trend analysis...")
                        x = np.arange(len(ts_data_clean))
                        slope = np.polyfit(x, ts_data_clean.values, 1)[0]
                        patterns = {
                            'name': metric,
                            'trend_direction': 'increasing' if slope > 0 else 'decreasing',
                            'trend_slope': float(slope),
                            'trend_mean': float(ts_data_clean.mean()),
                            'seasonal_amplitude': 0.0,
                            'resid_std': float(ts_data_clean.std())
                        }
                        daily_patterns[metric] = patterns
        
        self.patterns['daily_aggregated'] = daily_patterns
        return daily_patterns
    
    def save_patterns(self):
        """Save learned patterns to files"""
        print(f"\n{'='*80}")
        print("Saving Pattern Learning Results")
        print(f"{'='*80}")
        
        # Save state-level patterns
        if 'state_biometric' in self.patterns:
            state_patterns_summary = []
            for state, patterns in self.patterns['state_biometric'].items():
                summary = {
                    'state': state,
                    'trend_direction': patterns['trend_direction'],
                    'trend_slope': patterns['trend_slope'],
                    'trend_mean': patterns['trend_mean'],
                    'seasonal_amplitude': patterns['seasonal_amplitude'],
                    'resid_std': patterns['resid_std']
                }
                state_patterns_summary.append(summary)
            
            summary_df = pd.DataFrame(state_patterns_summary)
            output_file = self.output_path / 'state_patterns_summary.csv'
            summary_df.to_csv(output_file, index=False)
            print(f"  Saved: {output_file} ({len(summary_df)} states)")
        
        # Save daily aggregated patterns
        if 'daily_aggregated' in self.patterns:
            daily_patterns_summary = []
            for metric, patterns in self.patterns['daily_aggregated'].items():
                summary = {
                    'metric': metric,
                    'trend_direction': patterns['trend_direction'],
                    'trend_slope': patterns['trend_slope'],
                    'trend_mean': patterns['trend_mean'],
                    'seasonal_amplitude': patterns['seasonal_amplitude'],
                    'resid_std': patterns['resid_std']
                }
                daily_patterns_summary.append(summary)
            
            summary_df = pd.DataFrame(daily_patterns_summary)
            output_file = self.output_path / 'daily_patterns_summary.csv'
            summary_df.to_csv(output_file, index=False)
            print(f"  Saved: {output_file} ({len(summary_df)} metrics)")
        
        # Save full patterns as JSON (for reference)
        patterns_json = {}
        for key, value in self.patterns.items():
            # Convert to JSON-serializable format (remove full arrays, keep summaries)
            if isinstance(value, dict):
                json_value = {}
                for k, v in value.items():
                    if isinstance(v, dict):
                        json_value[k] = {
                            'trend_direction': v.get('trend_direction'),
                            'trend_slope': v.get('trend_slope'),
                            'trend_mean': v.get('trend_mean'),
                            'seasonal_amplitude': v.get('seasonal_amplitude'),
                            'resid_std': v.get('resid_std')
                        }
                    else:
                        json_value[k] = v
                patterns_json[key] = json_value
            else:
                patterns_json[key] = value
        
        output_file = self.output_path / 'patterns_summary.json'
        with open(output_file, 'w') as f:
            json.dump(patterns_json, f, indent=2)
        print(f"  Saved: {output_file}")
    
    def generate_pattern_insights(self):
        """Generate insights from learned patterns"""
        print(f"\n{'='*80}")
        print("Pattern Learning Insights")
        print(f"{'='*80}")
        
        insights = []
        
        # Daily aggregated insights
        if 'daily_aggregated' in self.patterns:
            print("\nDaily Aggregated Patterns:")
            for metric, patterns in self.patterns['daily_aggregated'].items():
                print(f"\n  {metric}:")
                print(f"    Trend: {patterns['trend_direction']} (slope: {patterns['trend_slope']:.2f})")
                print(f"    Seasonal amplitude: {patterns['seasonal_amplitude']:.2f}")
                print(f"    Residual std: {patterns['resid_std']:.2f}")
        
        # State-level insights
        if 'state_biometric' in self.patterns:
            print("\nState-Level Patterns (Sample):")
            state_count = 0
            for state, patterns in list(self.patterns['state_biometric'].items())[:5]:
                print(f"\n  {state}:")
                print(f"    Trend: {patterns['trend_direction']} (slope: {patterns['trend_slope']:.2f})")
                state_count += 1
        
        return insights
    
    def run_pattern_learning(self):
        """Execute complete pattern learning process"""
        print(f"\n{'='*80}")
        print("PATTERN LEARNING MODULE")
        print("Algorithm: STL Decomposition")
        print(f"{'='*80}")
        
        # Load data
        if not self.load_data():
            print("Failed to load data. Exiting.")
            return False
        
        # Learn patterns
        try:
            # Learn daily aggregated patterns (most important)
            self.learn_daily_aggregated_patterns()
            
            # Learn state-level patterns
            self.learn_state_level_patterns()
            
            # Generate insights
            self.generate_pattern_insights()
            
            # Save results
            self.save_patterns()
            
            print(f"\n{'='*80}")
            print("[SUCCESS] Pattern Learning Completed!")
            print(f"{'='*80}")
            print(f"\nResults saved to: {self.output_path}/")
            print("\nNext Steps:")
            print("  1. Review pattern summaries in CSV files")
            print("  2. Verify trend directions and seasonal patterns")
            print("  3. Proceed to Forecasting module")
            print(f"{'='*80}")
            
            return True
            
        except Exception as e:
            print(f"\n{'='*80}")
            print(f"ERROR: Pattern learning failed!")
            print(f"Error: {str(e)}")
            print(f"{'='*80}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main execution function"""
    learner = PatternLearner(
        data_path='processed_data',
        output_path='pattern_results'
    )
    
    success = learner.run_pattern_learning()
    
    if success:
        print("\n[SUCCESS] Pattern Learning module completed successfully!")
        print("Please review the results and test before proceeding to next feature.")
    else:
        print("\n[ERROR] Pattern Learning module failed. Please fix errors before proceeding.")


if __name__ == "__main__":
    main()
