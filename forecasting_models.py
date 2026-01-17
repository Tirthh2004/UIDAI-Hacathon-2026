"""
Forecasting Module - Auto ARIMA
AI-Driven Early Warning System for Aadhaar Update Surges

This module implements time-series forecasting using auto_ARIMA (pmdarima)
to predict upcoming update surges at state and daily aggregated levels.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from pmdarima import auto_arima
import warnings
import json
from datetime import datetime, timedelta
from sklearn.metrics import mean_absolute_error, mean_squared_error
import math
warnings.filterwarnings('ignore')


class ForecastModeler:
    """
    Forecast future values using auto_ARIMA
    
    Capability: Forecasting
    Algorithm: auto_ARIMA (pmdarima)
    Validation: Walk-forward validation
    """
    
    def __init__(self, data_path='processed_data', output_path='forecast_results'):
        """
        Initialize the Forecast Modeler
        
        Args:
            data_path: Path to processed data directory
            output_path: Path to save forecast results
        """
        self.data_path = Path(data_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(exist_ok=True)
        
        # Storage for forecasts
        self.forecasts = {}
        self.models = {}
        self.metrics = {}
        
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
            
            # Also load daily aggregated data if available
            analysis_path = Path('analysis_results')
            if (analysis_path / 'daily_aggregated_data.csv').exists():
                self.daily_df = pd.read_csv(
                    analysis_path / 'daily_aggregated_data.csv',
                    parse_dates=['date']
                )
            else:
                self.daily_df = None
            
            # Ensure date columns are datetime
            for df in [self.biometric_df, self.demographic_df, self.enrolment_df]:
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
            
            if self.daily_df is not None and 'date' in self.daily_df.columns:
                self.daily_df['date'] = pd.to_datetime(self.daily_df['date'])
            
            print(f"  Biometric: {len(self.biometric_df):,} rows")
            print(f"  Demographic: {len(self.demographic_df):,} rows")
            print(f"  Enrolment: {len(self.enrolment_df):,} rows")
            if self.daily_df is not None:
                print(f"  Daily Aggregated: {len(self.daily_df):,} rows")
            
            return True
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return False
    
    def prepare_time_series(self, df, group_cols, value_col, freq='D'):
        """
        Prepare time series data for forecasting
        
        Args:
            df: DataFrame with data
            group_cols: Columns to group by (e.g., ['state'], [])
            value_col: Column with values to aggregate
            freq: Frequency for time series ('D' for daily)
        
        Returns:
            Dictionary of time series (one per group)
        """
        time_series_dict = {}
        
        # Group and aggregate
        if len(group_cols) == 0:
            # Aggregate all data
            grouped = df.groupby('date')[value_col].sum().reset_index()
            grouped = grouped.sort_values('date')
            
            # Create complete date range
            min_date = grouped['date'].min()
            max_date = grouped['date'].max()
            date_range = pd.date_range(start=min_date, end=max_date, freq=freq)
            
            # Create time series with all dates
            ts_df = pd.DataFrame({'date': date_range})
            ts_df = ts_df.merge(grouped, on='date', how='left')
            ts_df[value_col] = ts_df[value_col].fillna(0)
            ts_df = ts_df.sort_values('date')
            
            # Extract values as numpy array
            time_series_dict['all'] = ts_df[value_col].values
            
        else:
            grouped = df.groupby(group_cols + ['date'])[value_col].sum().reset_index()
            grouped = grouped.sort_values(group_cols + ['date'])
            
            # Create date range
            min_date = grouped['date'].min()
            max_date = grouped['date'].max()
            date_range = pd.date_range(start=min_date, end=max_date, freq=freq)
            
            # Get unique groups
            if len(group_cols) == 1:
                groups = grouped[group_cols[0]].unique()
                for group in groups:
                    group_data = grouped[grouped[group_cols[0]] == group].copy()
                    
                    # Create complete date range for this group
                    ts_df = pd.DataFrame({'date': date_range})
                    ts_df = ts_df.merge(group_data[['date', value_col]], on='date', how='left')
                    ts_df[value_col] = ts_df[value_col].fillna(0)
                    ts_df = ts_df.sort_values('date')
                    
                    # Extract values
                    time_series_dict[str(group)] = ts_df[value_col].values
        
        return time_series_dict
    
    def calculate_metrics(self, actual, predicted):
        """
        Calculate forecast accuracy metrics
        
        Args:
            actual: Actual values
            predicted: Predicted values
        
        Returns:
            Dictionary with MAE, RMSE, MAPE
        """
        actual = np.array(actual)
        predicted = np.array(predicted)
        
        # Remove any NaN or inf values
        mask = np.isfinite(actual) & np.isfinite(predicted) & (actual != 0)
        actual = actual[mask]
        predicted = predicted[mask]
        
        if len(actual) == 0:
            return {'mae': np.nan, 'rmse': np.nan, 'mape': np.nan}
        
        mae = mean_absolute_error(actual, predicted)
        rmse = math.sqrt(mean_squared_error(actual, predicted))
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((actual - predicted) / (actual + 1e-8))) * 100
        
        return {'mae': mae, 'rmse': rmse, 'mape': mape}
    
    def forecast_with_arima(self, ts_data, forecast_periods, seasonal_period=None):
        """
        Forecast using auto_ARIMA
        
        Args:
            ts_data: Time series data (numpy array)
            forecast_periods: Number of periods to forecast
            seasonal_period: Seasonal period (e.g., 7 for weekly, None for non-seasonal)
        
        Returns:
            Dictionary with forecast, confidence intervals, and model info
        """
        try:
            # Remove any NaN or inf values
            ts_data = np.array(ts_data)
            ts_data = ts_data[np.isfinite(ts_data)]
            
            # Need at least some data points
            if len(ts_data) < 10:
                return None
            
            # Fit auto_ARIMA model
            model = auto_arima(
                ts_data,
                seasonal=True if seasonal_period else False,
                m=seasonal_period if seasonal_period else 1,
                stepwise=True,
                suppress_warnings=True,
                error_action='ignore',
                max_order=5,
                max_p=5,
                max_d=2,
                max_q=5,
                trace=False
            )
            
            # Generate forecast
            forecast, conf_int = model.predict(
                n_periods=forecast_periods,
                return_conf_int=True,
                alpha=0.05  # 95% confidence intervals
            )
            
            # Ensure forecast values are non-negative
            forecast = np.maximum(forecast, 0)
            conf_int = np.maximum(conf_int, 0)
            
            return {
                'forecast': forecast,
                'conf_int_lower': conf_int[:, 0],
                'conf_int_upper': conf_int[:, 1],
                'model_order': model.order,
                'model_seasonal_order': model.seasonal_order if seasonal_period else None,
                'aic': model.aic()
            }
            
        except Exception as e:
            print(f"    ARIMA forecasting error: {str(e)}")
            return None
    
    def forecast_daily_aggregated(self):
        """Forecast daily aggregated metrics"""
        print("\nForecasting Daily Aggregated Data...")
        
        if self.daily_df is None:
            print("  Daily aggregated data not available. Skipping.")
            return
        
        metrics_to_forecast = ['bio_total', 'demo_total', 'enrol_total']
        forecast_results = []
        
        for metric in metrics_to_forecast:
            print(f"  Forecasting {metric}...")
            
            # Prepare time series
            ts_dict = self.prepare_time_series(self.daily_df, [], metric, freq='D')
            
            if 'all' not in ts_dict:
                print(f"    Could not prepare time series for {metric}")
                continue
            
            ts_data = ts_dict['all']
            
            # Skip if insufficient data
            if len(ts_data) < 30:
                print(f"    Insufficient data for {metric} (need at least 30 days)")
                continue
            
            # Use last 80% for training, 20% for validation
            split_idx = int(len(ts_data) * 0.8)
            train_data = ts_data[:split_idx]
            test_data = ts_data[split_idx:]
            
            # Short-term forecast (1-3 months = 30-90 days)
            short_term_periods = min(90, len(test_data))
            if short_term_periods < 7:
                short_term_periods = 30  # Default to 30 days
            
            # Medium-term forecast (3-6 months = 90-180 days)
            medium_term_periods = min(180, len(test_data) * 2)
            
            # Forecast short-term
            print(f"    Short-term forecast ({short_term_periods} days)...")
            short_forecast = self.forecast_with_arima(train_data, short_term_periods, seasonal_period=7)
            
            if short_forecast:
                # Calculate metrics on test data
                test_forecast = short_forecast['forecast'][:len(test_data)]
                metrics = self.calculate_metrics(test_data, test_forecast)
                
                # Store results
                forecast_results.append({
                    'metric': metric,
                    'forecast_type': 'short_term',
                    'forecast_periods': short_term_periods,
                    'forecast_values': short_forecast['forecast'].tolist(),
                    'conf_lower': short_forecast['conf_int_lower'].tolist(),
                    'conf_upper': short_forecast['conf_int_upper'].tolist(),
                    'model_order': str(short_forecast['model_order']),
                    'aic': short_forecast['aic'],
                    'mae': metrics['mae'],
                    'rmse': metrics['rmse'],
                    'mape': metrics['mape']
                })
            
            # Forecast medium-term
            print(f"    Medium-term forecast ({medium_term_periods} days)...")
            medium_forecast = self.forecast_with_arima(train_data, medium_term_periods, seasonal_period=7)
            
            if medium_forecast:
                # Calculate metrics on test data (truncated to available test data)
                test_forecast_med = medium_forecast['forecast'][:len(test_data)]
                metrics_med = self.calculate_metrics(test_data, test_forecast_med)
                
                forecast_results.append({
                    'metric': metric,
                    'forecast_type': 'medium_term',
                    'forecast_periods': medium_term_periods,
                    'forecast_values': medium_forecast['forecast'].tolist(),
                    'conf_lower': medium_forecast['conf_int_lower'].tolist(),
                    'conf_upper': medium_forecast['conf_int_upper'].tolist(),
                    'model_order': str(medium_forecast['model_order']),
                    'aic': medium_forecast['aic'],
                    'mae': metrics_med['mae'],
                    'rmse': metrics_med['rmse'],
                    'mape': metrics_med['mape']
                })
        
        self.forecasts['daily_aggregated'] = forecast_results
        print(f"  Completed forecasting for {len(forecast_results)} series")
    
    def forecast_state_level(self, top_n_states=10):
        """Forecast state-level metrics"""
        print(f"\nForecasting State-Level Data (Top {top_n_states} states)...")
        
        # Calculate bio_total from age columns if not present
        if 'bio_total' not in self.biometric_df.columns:
            if 'bio_age_5_17' in self.biometric_df.columns and 'bio_age_17_' in self.biometric_df.columns:
                self.biometric_df['bio_total'] = self.biometric_df['bio_age_5_17'] + self.biometric_df['bio_age_17_']
            else:
                print("  ERROR: Cannot calculate bio_total - missing age columns")
                return
        
        # Get top states by total biometric updates
        state_totals = self.biometric_df.groupby('state')['bio_total'].sum().sort_values(ascending=False)
        top_states = state_totals.head(top_n_states).index.tolist()
        
        forecast_results = []
        
        for state in top_states:
            print(f"  Forecasting {state}...")
            
            # Prepare time series for biometric updates
            state_bio = self.biometric_df[self.biometric_df['state'] == state].copy()
            ts_dict = self.prepare_time_series(state_bio, [], 'bio_total', freq='D')
            
            if 'all' not in ts_dict:
                print(f"    Could not prepare time series for {state}")
                continue
            
            ts_data = ts_dict['all']
            
            # Skip if insufficient data
            if len(ts_data) < 30:
                print(f"    Insufficient data for {state} (need at least 30 days)")
                continue
            
            # Use last 80% for training
            split_idx = int(len(ts_data) * 0.8)
            train_data = ts_data[:split_idx]
            test_data = ts_data[split_idx:]
            
            # Short-term forecast (30-90 days)
            short_term_periods = min(90, len(test_data))
            if short_term_periods < 7:
                short_term_periods = 30
            
            print(f"    Short-term forecast ({short_term_periods} days)...")
            short_forecast = self.forecast_with_arima(train_data, short_term_periods, seasonal_period=7)
            
            if short_forecast:
                # Calculate metrics
                test_forecast = short_forecast['forecast'][:len(test_data)]
                metrics = self.calculate_metrics(test_data, test_forecast)
                
                forecast_results.append({
                    'state': state,
                    'forecast_type': 'short_term',
                    'forecast_periods': short_term_periods,
                    'forecast_values': short_forecast['forecast'].tolist(),
                    'conf_lower': short_forecast['conf_int_lower'].tolist(),
                    'conf_upper': short_forecast['conf_int_upper'].tolist(),
                    'model_order': str(short_forecast['model_order']),
                    'aic': short_forecast['aic'],
                    'mae': metrics['mae'],
                    'rmse': metrics['rmse'],
                    'mape': metrics['mape']
                })
        
        self.forecasts['state_level'] = forecast_results
        print(f"  Completed forecasting for {len(forecast_results)} states")
    
    def save_forecasts(self):
        """Save forecast results to CSV files"""
        print("\nSaving forecast results...")
        
        # Save daily aggregated forecasts
        if 'daily_aggregated' in self.forecasts:
            daily_forecasts = self.forecasts['daily_aggregated']
            
            # Create expanded format (one row per forecast period)
            expanded_daily = []
            for fc in daily_forecasts:
                periods = fc['forecast_periods']
                for i in range(periods):
                    expanded_daily.append({
                        'metric': fc['metric'],
                        'forecast_type': fc['forecast_type'],
                        'period': i + 1,
                        'forecast_value': fc['forecast_values'][i],
                        'conf_lower': fc['conf_lower'][i],
                        'conf_upper': fc['conf_upper'][i]
                    })
            
            if expanded_daily:
                daily_df = pd.DataFrame(expanded_daily)
                daily_df.to_csv(self.output_path / 'daily_forecasts.csv', index=False)
                print(f"  Saved daily forecasts: {len(expanded_daily)} rows")
            
            # Save summary
            daily_summary = pd.DataFrame([{k: v for k, v in fc.items() if k != 'forecast_values' and k != 'conf_lower' and k != 'conf_upper'} for fc in daily_forecasts])
            daily_summary.to_csv(self.output_path / 'daily_forecasts_summary.csv', index=False)
            print(f"  Saved daily forecasts summary: {len(daily_forecasts)} records")
        
        # Save state-level forecasts
        if 'state_level' in self.forecasts:
            state_forecasts = self.forecasts['state_level']
            
            # Create expanded format
            expanded_state = []
            for fc in state_forecasts:
                periods = fc['forecast_periods']
                for i in range(periods):
                    expanded_state.append({
                        'state': fc['state'],
                        'forecast_type': fc['forecast_type'],
                        'period': i + 1,
                        'forecast_value': fc['forecast_values'][i],
                        'conf_lower': fc['conf_lower'][i],
                        'conf_upper': fc['conf_upper'][i]
                    })
            
            if expanded_state:
                state_df = pd.DataFrame(expanded_state)
                state_df.to_csv(self.output_path / 'state_forecasts.csv', index=False)
                print(f"  Saved state forecasts: {len(expanded_state)} rows")
            
            # Save summary
            state_summary = pd.DataFrame([{k: v for k, v in fc.items() if k != 'forecast_values' and k != 'conf_lower' and k != 'conf_upper'} for fc in state_forecasts])
            state_summary.to_csv(self.output_path / 'state_forecasts_summary.csv', index=False)
            print(f"  Saved state forecasts summary: {len(state_forecasts)} records")
        
        # Save all forecasts as JSON
        forecasts_json = {}
        for key, value in self.forecasts.items():
            forecasts_json[key] = value
        
        with open(self.output_path / 'forecasts_summary.json', 'w') as f:
            json.dump(forecasts_json, f, indent=2, default=str)
        
        print(f"  Saved forecasts summary JSON")
    
    def run_forecasting(self):
        """Execute complete forecasting process"""
        print(f"\n{'='*80}")
        print("FORECASTING MODULE")
        print("Algorithm: auto_ARIMA (pmdarima)")
        print(f"{'='*80}")
        
        # Load data
        if not self.load_data():
            print("Failed to load data. Exiting.")
            return False
        
        # Generate forecasts
        try:
            # Forecast daily aggregated data
            self.forecast_daily_aggregated()
            
            # Forecast state-level data
            self.forecast_state_level(top_n_states=10)
            
            # Save results
            self.save_forecasts()
            
            print(f"\n{'='*80}")
            print("[SUCCESS] Forecasting Completed!")
            print(f"{'='*80}")
            print(f"\nResults saved to: {self.output_path}/")
            print("\nOutput Files:")
            print("  - daily_forecasts.csv: Detailed daily forecast values")
            print("  - daily_forecasts_summary.csv: Summary metrics for daily forecasts")
            print("  - state_forecasts.csv: Detailed state-level forecast values")
            print("  - state_forecasts_summary.csv: Summary metrics for state forecasts")
            print("  - forecasts_summary.json: Complete forecast results in JSON format")
            print(f"{'='*80}")
            
            return True
            
        except Exception as e:
            print(f"\n{'='*80}")
            print(f"ERROR: Forecasting failed!")
            print(f"Error: {str(e)}")
            print(f"{'='*80}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main execution function"""
    modeler = ForecastModeler(
        data_path='processed_data',
        output_path='forecast_results'
    )
    
    success = modeler.run_forecasting()
    
    if success:
        print("\n[SUCCESS] Forecasting module completed successfully!")
        print("Please review the results and test before proceeding to next feature.")
    else:
        print("\n[ERROR] Forecasting module failed. Please fix errors before proceeding.")


if __name__ == "__main__":
    main()
