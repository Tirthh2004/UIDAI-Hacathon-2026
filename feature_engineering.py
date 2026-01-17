"""
Feature Engineering Module
AI-Driven Early Warning System for Aadhaar Update Surges

This module creates features for ML models:
- Lag features (1, 7, 30 days)
- Rolling statistics (mean, std, min, max)
- Seasonal features (cyclic encoding)
- Z-Score comparison (compare to baseline)
- IQR comparison
- StandardScaler normalization
- Geographic aggregations
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
import warnings
import json
from datetime import datetime
warnings.filterwarnings('ignore')


class FeatureEngineer:
    """
    Create features for machine learning models
    
    Capability: Feature Engineering
    Techniques: Lag features, Rolling stats, Seasonal features, Scaling, Comparisons
    """
    
    def __init__(self, data_path='processed_data', output_path='feature_results'):
        """
        Initialize the Feature Engineer
        
        Args:
            data_path: Path to processed data directory
            output_path: Path to save feature engineering results
        """
        self.data_path = Path(data_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(exist_ok=True)
        
        # Feature engineering parameters
        self.lag_periods = [1, 7, 30]  # Lag features
        self.rolling_windows = [7, 14, 30]  # Rolling statistics windows
        
        # Storage for features
        self.features = {}
        self.scalers = {}
        
    def load_data(self):
        """Load cleaned data files and analysis results"""
        print("Loading data...")
        try:
            # Load analysis results
            analysis_path = Path('analysis_results')
            if (analysis_path / 'daily_aggregated_data.csv').exists():
                self.daily_df = pd.read_csv(
                    analysis_path / 'daily_aggregated_data.csv',
                    parse_dates=['date']
                )
            else:
                self.daily_df = None
            
            if (analysis_path / 'state_level_analysis.csv').exists():
                self.state_df = pd.read_csv(analysis_path / 'state_level_analysis.csv')
            else:
                self.state_df = None
            
            if (analysis_path / 'district_coverage_analysis.csv').exists():
                self.district_df = pd.read_csv(analysis_path / 'district_coverage_analysis.csv')
            else:
                self.district_df = None
            
            # Load raw data for detailed features
            self.biometric_df = pd.read_csv(
                self.data_path / 'biometric_cleaned.csv',
                parse_dates=['date']
            )
            
            if self.daily_df is not None and 'date' in self.daily_df.columns:
                self.daily_df['date'] = pd.to_datetime(self.daily_df['date'])
            
            print(f"  Daily Aggregated: {len(self.daily_df):,} rows" if self.daily_df is not None else "  Daily Aggregated: Not available")
            if self.state_df is not None:
                print(f"  State Level: {len(self.state_df):,} rows")
            if self.district_df is not None:
                print(f"  District Level: {len(self.district_df):,} rows")
            
            return True
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return False
    
    def create_lag_features(self, df, value_col, date_col='date'):
        """
        Create lag features (previous day/week/month values)
        
        Args:
            df: DataFrame with time series data
            value_col: Column name with values
            date_col: Column name with dates
            
        Returns:
            DataFrame with lag features added
        """
        df = df.copy().sort_values(date_col).reset_index(drop=True)
        
        for lag in self.lag_periods:
            df[f'{value_col}_lag_{lag}'] = df[value_col].shift(lag)
        
        return df
    
    def create_rolling_statistics(self, df, value_col, date_col='date'):
        """
        Create rolling statistics features
        
        Args:
            df: DataFrame with time series data
            value_col: Column name with values
            date_col: Column name with dates
            
        Returns:
            DataFrame with rolling statistics added
        """
        df = df.copy().sort_values(date_col).reset_index(drop=True)
        
        for window in self.rolling_windows:
            # Rolling mean
            df[f'{value_col}_rolling_mean_{window}'] = df[value_col].rolling(window=window, min_periods=1).mean()
            
            # Rolling std
            df[f'{value_col}_rolling_std_{window}'] = df[value_col].rolling(window=window, min_periods=1).std()
            
            # Rolling min
            df[f'{value_col}_rolling_min_{window}'] = df[value_col].rolling(window=window, min_periods=1).min()
            
            # Rolling max
            df[f'{value_col}_rolling_max_{window}'] = df[value_col].rolling(window=window, min_periods=1).max()
            
            # Rolling median
            df[f'{value_col}_rolling_median_{window}'] = df[value_col].rolling(window=window, min_periods=1).median()
        
        return df
    
    def create_seasonal_features(self, df, date_col='date'):
        """
        Create seasonal features (cyclic encoding)
        
        Args:
            df: DataFrame with date column
            date_col: Column name with dates
            
        Returns:
            DataFrame with seasonal features added
        """
        df = df.copy()
        
        if date_col not in df.columns:
            return df
        
        df[date_col] = pd.to_datetime(df[date_col])
        
        # Day of week (0=Monday, 6=Sunday)
        df['day_of_week'] = df[date_col].dt.dayofweek
        
        # Cyclic encoding for day of week (sin/cos)
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Month (1-12)
        df['month'] = df[date_col].dt.month
        
        # Cyclic encoding for month (sin/cos)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Quarter (1-4)
        df['quarter'] = df[date_col].dt.quarter
        
        # Week of year
        df['week_of_year'] = df[date_col].dt.isocalendar().week
        
        # Day of month
        df['day_of_month'] = df[date_col].dt.day
        
        # Year
        df['year'] = df[date_col].dt.year
        
        return df
    
    def create_z_score_comparison(self, df, value_col, baseline_col=None):
        """
        Create Z-score comparison features (compare to baseline)
        
        Args:
            df: DataFrame with values
            value_col: Column name with current values
            baseline_col: Column name with baseline (if None, uses rolling mean)
            
        Returns:
            DataFrame with Z-score features added
        """
        df = df.copy()
        
        if baseline_col is None:
            # Use rolling mean as baseline
            baseline_col = f'{value_col}_rolling_mean_30'
            if baseline_col not in df.columns:
                df[baseline_col] = df[value_col].rolling(window=30, min_periods=1).mean()
        
        if baseline_col in df.columns:
            # Calculate baseline statistics
            baseline_mean = df[baseline_col].mean()
            baseline_std = df[baseline_col].std()
            
            if baseline_std > 0:
                df[f'{value_col}_z_score'] = (df[value_col] - baseline_mean) / baseline_std
            else:
                df[f'{value_col}_z_score'] = 0.0
            
            # Deviation from baseline
            df[f'{value_col}_deviation_from_baseline'] = df[value_col] - df[baseline_col]
            df[f'{value_col}_pct_change_from_baseline'] = ((df[value_col] - df[baseline_col]) / (df[baseline_col] + 1)) * 100
        
        return df
    
    def create_iqr_comparison(self, df, value_col):
        """
        Create IQR comparison features
        
        Args:
            df: DataFrame with values
            value_col: Column name with values
            
        Returns:
            DataFrame with IQR comparison features added
        """
        df = df.copy()
        
        # Calculate IQR for rolling window
        rolling_q1 = df[value_col].rolling(window=30, min_periods=1).quantile(0.25)
        rolling_q3 = df[value_col].rolling(window=30, min_periods=1).quantile(0.75)
        rolling_iqr = rolling_q3 - rolling_q1
        
        df[f'{value_col}_iqr_q1'] = rolling_q1
        df[f'{value_col}_iqr_q3'] = rolling_q3
        df[f'{value_col}_iqr'] = rolling_iqr
        
        # IQR bounds
        df[f'{value_col}_iqr_lower_bound'] = rolling_q1 - 1.5 * rolling_iqr
        df[f'{value_col}_iqr_upper_bound'] = rolling_q3 + 1.5 * rolling_iqr
        
        # Check if value is outside IQR bounds
        df[f'{value_col}_outside_iqr'] = (
            (df[value_col] < df[f'{value_col}_iqr_lower_bound']) | 
            (df[value_col] > df[f'{value_col}_iqr_upper_bound'])
        ).astype(int)
        
        return df
    
    def apply_standard_scaler(self, df, feature_cols):
        """
        Apply StandardScaler to features
        
        Args:
            df: DataFrame with features
            feature_cols: List of column names to scale
            
        Returns:
            Tuple of (DataFrame with scaled features, fitted scaler)
        """
        df = df.copy()
        
        # Filter to only existing columns
        feature_cols = [col for col in feature_cols if col in df.columns]
        
        if len(feature_cols) == 0:
            return df, None
        
        # Remove NaN values for scaling
        df_scaled = df[feature_cols].fillna(0)
        
        # Fit scaler
        scaler = StandardScaler()
        scaled_values = scaler.fit_transform(df_scaled)
        
        # Create DataFrame with scaled values
        scaled_df = pd.DataFrame(scaled_values, columns=feature_cols, index=df.index)
        
        # Add scaled columns to original dataframe
        for col in feature_cols:
            df[f'{col}_scaled'] = scaled_df[col]
        
        return df, scaler
    
    def create_geographic_features(self, df, geo_level='state'):
        """
        Create geographic aggregation features
        
        Args:
            df: DataFrame with geographic data
            geo_level: Geographic level ('state' or 'district')
            
        Returns:
            DataFrame with geographic features added
        """
        if geo_level == 'state' and self.state_df is not None:
            state_df = self.state_df.copy()
            
            # State-level aggregations
            if 'bio_total' in state_df.columns:
                state_df['state_bio_total_rank'] = state_df['bio_total'].rank(ascending=False)
                state_df['state_bio_total_pct_of_total'] = (state_df['bio_total'] / state_df['bio_total'].sum()) * 100
            
            if 'demo_total' in state_df.columns:
                state_df['state_demo_total_rank'] = state_df['demo_total'].rank(ascending=False)
                state_df['state_demo_total_pct_of_total'] = (state_df['demo_total'] / state_df['demo_total'].sum()) * 100
            
            return state_df
        
        elif geo_level == 'district' and self.district_df is not None:
            district_df = self.district_df.copy()
            
            # District-level aggregations by state
            if 'state' in district_df.columns and 'bio_total' in district_df.columns:
                district_df['district_bio_total_rank_by_state'] = district_df.groupby('state')['bio_total'].rank(ascending=False)
                
                state_totals = district_df.groupby('state')['bio_total'].transform('sum')
                district_df['district_bio_total_pct_of_state'] = (district_df['bio_total'] / (state_totals + 1)) * 100
            
            return district_df
        
        return df
    
    def engineer_daily_features(self):
        """
        Engineer features for daily aggregated data
        
        Returns:
            DataFrame with engineered features
        """
        print("\nEngineering features for daily aggregated data...")
        
        if self.daily_df is None:
            print("  Daily aggregated data not available")
            return pd.DataFrame()
        
        df = self.daily_df.copy()
        df = df.sort_values('date').reset_index(drop=True)
        
        metrics = ['bio_total', 'demo_total', 'enrol_total']
        feature_dfs = []
        
        for metric in metrics:
            if metric not in df.columns:
                continue
            
            metric_df = df[['date', metric]].copy()
            
            # Create lag features
            metric_df = self.create_lag_features(metric_df, metric)
            
            # Create rolling statistics
            metric_df = self.create_rolling_statistics(metric_df, metric)
            
            # Create Z-score comparison
            metric_df = self.create_z_score_comparison(metric_df, metric)
            
            # Create IQR comparison
            metric_df = self.create_iqr_comparison(metric_df, metric)
            
            # Keep only new feature columns (except date and original metric)
            new_cols = [col for col in metric_df.columns if col not in ['date', metric]]
            
            # Merge back to main dataframe
            for col in new_cols:
                if col not in df.columns:
                    df[col] = metric_df[col]
        
        # Add seasonal features
        df = self.create_seasonal_features(df, 'date')
        
        print(f"  Created {len([col for col in df.columns if col not in self.daily_df.columns])} new features")
        
        return df
    
    def engineer_state_features(self):
        """
        Engineer features for state-level data
        
        Returns:
            DataFrame with engineered features
        """
        print("\nEngineering features for state-level data...")
        
        if self.state_df is None:
            print("  State-level data not available")
            return pd.DataFrame()
        
        df = self.create_geographic_features(self.state_df, 'state')
        
        # Apply StandardScaler to numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'state' in df.columns:
            numeric_cols = [col for col in numeric_cols if col != 'state']
        
        if len(numeric_cols) > 0:
            df, scaler = self.apply_standard_scaler(df, numeric_cols[:10])  # Limit to first 10 to avoid too many features
            if scaler:
                self.scalers['state'] = scaler
        
        print(f"  Created {len([col for col in df.columns if col not in self.state_df.columns])} new features")
        
        return df
    
    def run_feature_engineering(self):
        """
        Run complete feature engineering pipeline
        
        Returns:
            Dictionary with engineered features
        """
        print(f"\n{'='*80}")
        print("FEATURE ENGINEERING")
        print(f"{'='*80}")
        
        features = {}
        
        # Daily features
        daily_features = self.engineer_daily_features()
        if len(daily_features) > 0:
            features['daily'] = daily_features
        
        # State features
        state_features = self.engineer_state_features()
        if len(state_features) > 0:
            features['state'] = state_features
        
        return features
    
    def save_results(self, features):
        """
        Save feature engineering results to files
        
        Args:
            features: Dictionary with engineered features
        """
        print(f"\n{'='*80}")
        print("SAVING RESULTS")
        print(f"{'='*80}")
        
        for feature_type, feature_df in features.items():
            if len(feature_df) > 0:
                output_file = self.output_path / f'features_{feature_type}.csv'
                feature_df.to_csv(output_file, index=False)
                print(f"\n[SUCCESS] Saved: {output_file}")
                print(f"   Rows: {len(feature_df)}, Columns: {len(feature_df.columns)}")
        
        # Create feature summary
        summary = {
            'feature_engineering_date': datetime.now().isoformat(),
            'parameters': {
                'lag_periods': self.lag_periods,
                'rolling_windows': self.rolling_windows
            },
            'feature_counts': {},
            'feature_types': {}
        }
        
        for feature_type, feature_df in features.items():
            if len(feature_df) > 0:
                summary['feature_counts'][feature_type] = {
                    'num_rows': len(feature_df),
                    'num_columns': len(feature_df.columns),
                    'num_features_created': len(feature_df.columns) - len(getattr(self, f'{feature_type}_df', pd.DataFrame()).columns) if hasattr(self, f'{feature_type}_df') else len(feature_df.columns)
                }
                
                # Categorize features
                feature_cols = feature_df.columns.tolist()
                summary['feature_types'][feature_type] = {
                    'lag_features': len([c for c in feature_cols if '_lag_' in c]),
                    'rolling_features': len([c for c in feature_cols if '_rolling_' in c]),
                    'seasonal_features': len([c for c in feature_cols if any(x in c for x in ['day_of_week', 'month', 'quarter', 'week_of_year'])]),
                    'z_score_features': len([c for c in feature_cols if '_z_score' in c]),
                    'iqr_features': len([c for c in feature_cols if '_iqr' in c]),
                    'scaled_features': len([c for c in feature_cols if '_scaled' in c]),
                    'geographic_features': len([c for c in feature_cols if any(x in c for x in ['_rank', '_pct_of_'])]),
                }
        
        # Save summary JSON
        summary_file = self.output_path / 'feature_engineering_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n[SUCCESS] Saved: {summary_file}")
    
    def run(self):
        """Run the complete feature engineering pipeline"""
        if not self.load_data():
            return False
        
        features = self.run_feature_engineering()
        self.save_results(features)
        
        print(f"\n{'='*80}")
        print("[SUCCESS] Feature Engineering Completed!")
        print(f"{'='*80}")
        
        return True


if __name__ == "__main__":
    engineer = FeatureEngineer()
    engineer.run()
