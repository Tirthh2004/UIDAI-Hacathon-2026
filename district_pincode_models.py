"""
District & Pincode Level Models Module
AI-Driven Early Warning System for Aadhaar Update Surges

This module extends forecasting and anomaly detection to granular levels:
- District-level forecasting
- Pincode-level anomaly detection
- High-volume vs low-volume area handling
- Aggregated predictions for resource planning
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import json
from datetime import datetime
warnings.filterwarnings('ignore')


class DistrictPincodeModeler:
    """
    District and Pincode level forecasting and anomaly detection
    
    Capability: Granular Modeling
    Extensions: Forecasting (district-level), Anomaly Detection (pincode-level)
    """
    
    def __init__(self, data_path='processed_data', output_path='district_pincode_results'):
        """
        Initialize the District & Pincode Modeler
        
        Args:
            data_path: Path to processed data directory
            output_path: Path to save results
        """
        self.data_path = Path(data_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(exist_ok=True)
        
        # Parameters for high vs low volume handling
        self.high_volume_threshold_percentile = 75  # Top 25% are high volume
        self.min_data_points_district = 10  # Minimum data points for district forecasting (optimized for speed)
        self.min_data_points_pincode = 5  # Minimum data points for pincode anomaly detection
        self.top_districts_per_state = 3  # Forecast top N districts per state (optimized for speed)
        self.top_pincodes_overall = 30  # Analyze top N pincodes (optimized for speed)
        
    def load_data(self):
        """Load cleaned data files"""
        print("Loading data...")
        try:
            self.biometric_df = pd.read_csv(
                self.data_path / 'biometric_cleaned.csv',
                parse_dates=['date']
            )
            self.demographic_df = pd.read_csv(
                self.data_path / 'demographic_cleaned.csv',
                parse_dates=['date']
            )
            
            # Ensure date columns are datetime
            for df in [self.biometric_df, self.demographic_df]:
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
            
            # Calculate totals
            if 'bio_total' not in self.biometric_df.columns:
                if 'bio_age_5_17' in self.biometric_df.columns and 'bio_age_17_' in self.biometric_df.columns:
                    self.biometric_df['bio_total'] = self.biometric_df['bio_age_5_17'] + self.biometric_df['bio_age_17_']
            
            if 'demo_total' not in self.demographic_df.columns:
                if 'demo_age_5_17' in self.demographic_df.columns and 'demo_age_17_' in self.demographic_df.columns:
                    self.demographic_df['demo_total'] = self.demographic_df['demo_age_5_17'] + self.demographic_df['demo_age_17_']
            
            print(f"  Biometric: {len(self.biometric_df):,} rows")
            print(f"  Demographic: {len(self.demographic_df):,} rows")
            
            return True
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return False
    
    def classify_volume_levels(self, df, group_cols, value_col):
        """
        Classify areas as high-volume or low-volume
        
        Args:
            df: DataFrame with data
            group_cols: Columns to group by (e.g., ['district'], ['pincode'])
            value_col: Column with values to analyze
            
        Returns:
            DataFrame with volume_classification column
        """
        geo_df = df.groupby(group_cols)[value_col].sum().reset_index()
        geo_df.columns = list(group_cols) + [value_col]
        
        threshold = np.percentile(geo_df[value_col], self.high_volume_threshold_percentile)
        geo_df['volume_classification'] = geo_df[value_col].apply(
            lambda x: 'high_volume' if x >= threshold else 'low_volume'
        )
        
        return geo_df
    
    def forecast_district_level(self, metric='bio_total', top_districts_per_state=10):
        """
        Forecast at district level (extending state-level forecasting)
        
        Args:
            metric: Metric to forecast (bio_total, demo_total)
            top_districts_per_state: Number of top districts per state to forecast
            
        Returns:
            DataFrame with district forecasts
        """
        print(f"\nForecasting district-level {metric}...")
        
        # Select appropriate dataframe
        if 'bio' in metric:
            df = self.biometric_df.copy()
        elif 'demo' in metric:
            df = self.demographic_df.copy()
        else:
            return pd.DataFrame()
        
        if metric not in df.columns:
            print(f"  Metric {metric} not found in data")
            return pd.DataFrame()
        
        # Get district totals
        district_totals = df.groupby(['state', 'district'])[metric].sum().reset_index()
        district_totals.columns = ['state', 'district', 'total']
        
        # Classify volume levels
        district_totals = self.classify_volume_levels(
            df, ['state', 'district'], metric
        )
        
        forecast_results = []
        
        # Process each state (limit to top 10 states for faster processing)
        states = district_totals.groupby('state')[metric].sum().sort_values(ascending=False).head(10).index.tolist()
        print(f"  Processing top {len(states)} states (for faster processing)...")
        
        for state in states:
            state_districts = district_totals[district_totals['state'] == state].copy()
            state_districts = state_districts.sort_values(metric, ascending=False)
            
            # Get top districts per state
            top_districts = state_districts.head(top_districts_per_state)
            
            for idx, district_row in top_districts.iterrows():
                district = district_row['district']
                volume_class = district_row['volume_classification']
                
                # Get time series for this district
                district_data = df[(df['state'] == state) & (df['district'] == district)].copy()
                district_daily = district_data.groupby('date')[metric].sum().reset_index()
                district_daily = district_daily.sort_values('date')
                district_daily = district_daily.set_index('date')[metric]
                
                if len(district_daily) < self.min_data_points_district:
                    continue
                
                # Prepare time series
                ts_data = district_daily.values
                
                # Adjust parameters based on volume classification
                if volume_class == 'high_volume':
                    forecast_periods = 30  # 30 days for high-volume
                else:
                    forecast_periods = 14  # 14 days for low-volume (less data)
                
                try:
                    # Use simpler forecasting method for speed (moving average + trend)
                    # This is much faster than ARIMA while still providing useful forecasts
                    historical_mean = district_daily.mean()
                    historical_std = district_daily.std()
                    
                    # Calculate trend from recent data (last 30% of data)
                    recent_data = ts_data[-max(3, len(ts_data)//3):]
                    if len(recent_data) > 1:
                        trend_slope = (recent_data[-1] - recent_data[0]) / len(recent_data)
                    else:
                        trend_slope = 0
                    
                    # Simple forecast: mean + trend projection
                    forecast_base = historical_mean
                    forecast_values = [forecast_base + trend_slope * (i+1) for i in range(forecast_periods)]
                    forecast_values = np.maximum(forecast_values, 0)  # Ensure non-negative
                    
                    # Calculate forecast metrics
                    mean_forecast = np.mean(forecast_values)
                    max_forecast = np.max(forecast_values)
                    trend = trend_slope
                    
                    # Simple confidence intervals (based on historical std)
                    confidence_lower = mean_forecast - 1.96 * historical_std / np.sqrt(forecast_periods)
                    confidence_upper = mean_forecast + 1.96 * historical_std / np.sqrt(forecast_periods)
                    confidence_lower = max(0, confidence_lower)
                    
                    forecast_results.append({
                        'state': state,
                        'district': district,
                        'metric': metric,
                        'volume_classification': volume_class,
                        'historical_mean': historical_mean,
                        'historical_total': district_daily.sum(),
                        'forecast_periods': forecast_periods,
                        'forecast_mean': mean_forecast,
                        'forecast_max': max_forecast,
                        'forecast_trend': trend,
                        'confidence_lower': confidence_lower,
                        'confidence_upper': confidence_upper,
                        'model_order': 'simple_trend',  # Simplified model
                        'data_points': len(district_daily)
                    })
                    
                except Exception as e:
                    continue
        
        forecasts_df = pd.DataFrame(forecast_results)
        print(f"  Generated {len(forecasts_df)} district forecasts")
        
        return forecasts_df
    
    def detect_pincode_anomalies(self, metric='bio_total'):
        """
        Detect anomalies at pincode level (extending geographic anomaly detection)
        
        Args:
            metric: Metric to analyze (bio_total, demo_total)
            
        Returns:
            DataFrame with pincode anomalies
        """
        print(f"\nDetecting pincode-level anomalies for {metric}...")
        
        # Select appropriate dataframe
        if 'bio' in metric:
            df = self.biometric_df.copy()
        elif 'demo' in metric:
            df = self.demographic_df.copy()
        else:
            return pd.DataFrame()
        
        if metric not in df.columns:
            print(f"  Metric {metric} not found in data")
            return pd.DataFrame()
        
        # Get pincode totals
        pincode_totals = df.groupby(['state', 'district', 'pincode'])[metric].sum().reset_index()
        pincode_totals.columns = ['state', 'district', 'pincode', metric]
        
        # Classify volume levels
        pincode_totals['volume_classification'] = pincode_totals[metric].apply(
            lambda x: 'high_volume' if x >= np.percentile(pincode_totals[metric], self.high_volume_threshold_percentile) else 'low_volume'
        )
        
        # Get top pincodes for analysis
        top_pincodes = pincode_totals.nlargest(self.top_pincodes_overall, metric)
        
        anomalies_list = []
        
        # Calculate IQR bounds for each volume class
        for volume_class in ['high_volume', 'low_volume']:
            volume_data = pincode_totals[pincode_totals['volume_classification'] == volume_class][metric].values
            
            if len(volume_data) < 4:
                continue
            
            q1 = np.percentile(volume_data, 25)
            q3 = np.percentile(volume_data, 75)
            iqr = q3 - q1
            
            if iqr == 0:
                continue
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            # Check top pincodes for anomalies
            volume_pincodes = top_pincodes[top_pincodes['volume_classification'] == volume_class]
            
            for idx, row in volume_pincodes.iterrows():
                value = row[metric]
                is_anomaly = (value < lower_bound) or (value > upper_bound)
                
                if is_anomaly:
                    # Calculate MAD Z-score
                    median = np.median(volume_data)
                    mad = np.median(np.abs(volume_data - median))
                    if mad > 0:
                        mad_z_score = 0.6745 * (value - median) / mad
                    else:
                        mad_z_score = 0.0
                    
                    # Calculate severity
                    if value > upper_bound:
                        deviation = (value - upper_bound) / iqr if iqr > 0 else 0
                        severity = min(1.0, deviation / 2.0)
                    else:
                        deviation = (lower_bound - value) / iqr if iqr > 0 else 0
                        severity = min(1.0, deviation / 2.0)
                    
                    anomalies_list.append({
                        'pincode': row['pincode'],
                        'state': row['state'],
                        'district': row['district'],
                        'metric': metric,
                        'value': value,
                        'volume_classification': volume_class,
                        'iqr_lower_bound': lower_bound,
                        'iqr_upper_bound': upper_bound,
                        'iqr_deviation': deviation,
                        'mad_z_score': mad_z_score,
                        'severity': severity,
                        'is_high_anomaly': value > upper_bound
                    })
        
        anomalies_df = pd.DataFrame(anomalies_list)
        print(f"  Found {len(anomalies_df)} pincode-level anomalies")
        
        return anomalies_df
    
    def aggregate_predictions_for_planning(self, district_forecasts_df):
        """
        Aggregate district forecasts for resource planning
        
        Args:
            district_forecasts_df: DataFrame with district forecasts
            
        Returns:
            DataFrame with aggregated predictions
        """
        print("\nAggregating predictions for resource planning...")
        
        if len(district_forecasts_df) == 0:
            return pd.DataFrame()
        
        # Aggregate by state
        state_aggregations = district_forecasts_df.groupby('state').agg({
            'forecast_mean': 'sum',
            'forecast_max': 'sum',
            'historical_total': 'sum',
            'district': 'count'
        }).reset_index()
        state_aggregations.columns = ['state', 'total_forecast_mean', 'total_forecast_max', 
                                     'total_historical', 'num_districts_forecasted']
        
        # Calculate forecast increase
        state_aggregations['forecast_increase'] = (
            (state_aggregations['total_forecast_mean'] - state_aggregations['total_historical']) / 
            (state_aggregations['total_historical'] + 1) * 100
        )
        
        # Aggregate by volume classification
        volume_aggregations = district_forecasts_df.groupby(['state', 'volume_classification']).agg({
            'forecast_mean': 'sum',
            'district': 'count'
        }).reset_index()
        volume_aggregations.columns = ['state', 'volume_classification', 'forecast_total', 'num_districts']
        
        return state_aggregations, volume_aggregations
    
    def run_all_models(self):
        """
        Run district and pincode level modeling
        
        Returns:
            Dictionary with all results
        """
        print(f"\n{'='*80}")
        print("DISTRICT & PINCODE LEVEL MODELS")
        print(f"{'='*80}")
        
        results = {}
        
        # District-level forecasting
        metrics = ['bio_total', 'demo_total']
        district_forecasts_list = []
        
        for metric in metrics:
            forecasts_df = self.forecast_district_level(metric, self.top_districts_per_state)
            if len(forecasts_df) > 0:
                district_forecasts_list.append(forecasts_df)
        
        if district_forecasts_list:
            results['district_forecasts'] = pd.concat(district_forecasts_list, ignore_index=True)
        
        # Pincode-level anomaly detection
        pincode_anomalies_list = []
        for metric in metrics:
            anomalies_df = self.detect_pincode_anomalies(metric)
            if len(anomalies_df) > 0:
                pincode_anomalies_list.append(anomalies_df)
        
        if pincode_anomalies_list:
            results['pincode_anomalies'] = pd.concat(pincode_anomalies_list, ignore_index=True)
        
        # Aggregate predictions for resource planning
        if 'district_forecasts' in results:
            state_agg, volume_agg = self.aggregate_predictions_for_planning(results['district_forecasts'])
            results['state_aggregations'] = state_agg
            results['volume_aggregations'] = volume_agg
        
        return results
    
    def save_results(self, results):
        """
        Save district and pincode model results
        
        Args:
            results: Dictionary with model results
        """
        print(f"\n{'='*80}")
        print("SAVING RESULTS")
        print(f"{'='*80}")
        
        # Save district forecasts
        if 'district_forecasts' in results:
            output_file = self.output_path / 'district_forecasts.csv'
            results['district_forecasts'].to_csv(output_file, index=False)
            print(f"\n[SUCCESS] Saved: {output_file}")
            print(f"   Total district forecasts: {len(results['district_forecasts'])}")
        
        # Save pincode anomalies
        if 'pincode_anomalies' in results:
            output_file = self.output_path / 'pincode_anomalies.csv'
            results['pincode_anomalies'].to_csv(output_file, index=False)
            print(f"[SUCCESS] Saved: {output_file}")
            print(f"   Total pincode anomalies: {len(results['pincode_anomalies'])}")
        
        # Save aggregations
        if 'state_aggregations' in results:
            output_file = self.output_path / 'state_aggregations.csv'
            results['state_aggregations'].to_csv(output_file, index=False)
            print(f"[SUCCESS] Saved: {output_file}")
        
        if 'volume_aggregations' in results:
            output_file = self.output_path / 'volume_aggregations.csv'
            results['volume_aggregations'].to_csv(output_file, index=False)
            print(f"[SUCCESS] Saved: {output_file}")
        
        # Create summary
        summary = {
            'modeling_date': datetime.now().isoformat(),
            'parameters': {
                'high_volume_threshold_percentile': self.high_volume_threshold_percentile,
                'min_data_points_district': self.min_data_points_district,
                'min_data_points_pincode': self.min_data_points_pincode,
                'top_districts_per_state': self.top_districts_per_state,
                'top_pincodes_overall': self.top_pincodes_overall
            },
            'summary': {}
        }
        
        if 'district_forecasts' in results:
            df = results['district_forecasts']
            summary['summary']['district_forecasts'] = {
                'total_forecasts': len(df),
                'unique_states': df['state'].nunique() if 'state' in df.columns else 0,
                'unique_districts': df['district'].nunique() if 'district' in df.columns else 0,
                'high_volume_count': len(df[df['volume_classification'] == 'high_volume']) if 'volume_classification' in df.columns else 0,
                'low_volume_count': len(df[df['volume_classification'] == 'low_volume']) if 'volume_classification' in df.columns else 0
            }
        
        if 'pincode_anomalies' in results:
            df = results['pincode_anomalies']
            summary['summary']['pincode_anomalies'] = {
                'total_anomalies': len(df),
                'unique_pincodes': df['pincode'].nunique() if 'pincode' in df.columns else 0,
                'unique_states': df['state'].nunique() if 'state' in df.columns else 0,
                'high_severity': len(df[df['severity'] >= 0.7]) if 'severity' in df.columns else 0
            }
        
        # Save summary JSON
        summary_file = self.output_path / 'district_pincode_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"[SUCCESS] Saved: {summary_file}")
    
    def run(self):
        """Run the complete district and pincode modeling pipeline"""
        if not self.load_data():
            return False
        
        results = self.run_all_models()
        self.save_results(results)
        
        print(f"\n{'='*80}")
        print("[SUCCESS] District & Pincode Level Models Completed!")
        print(f"{'='*80}")
        
        return True


if __name__ == "__main__":
    modeler = DistrictPincodeModeler()
    modeler.run()
