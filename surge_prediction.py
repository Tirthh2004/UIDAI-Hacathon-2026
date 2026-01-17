"""
Surge Prediction Module
AI-Driven Early Warning System for Aadhaar Update Surges

This module predicts upcoming surges in update demand using:
- Age transition analysis (children turning 5, 18)
- Historical surge pattern identification
- Forecasting integration
- Regional surge patterns
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import json
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')


class SurgePredictor:
    """
    Predict upcoming surges in update demand
    
    Capability: Surge Prediction
    Indicators: Age transitions, Historical patterns, Regional patterns
    """
    
    def __init__(self, data_path='processed_data', output_path='surge_results'):
        """
        Initialize the Surge Predictor
        
        Args:
            data_path: Path to processed data directory
            output_path: Path to save surge prediction results
        """
        self.data_path = Path(data_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(exist_ok=True)
        
        # Surge prediction parameters
        self.surge_threshold_multiplier = 1.5  # Surge is X times the average
        self.forecast_horizon_days = 90  # Predict surges up to 90 days ahead
        self.min_surge_confidence = 0.5  # Minimum confidence for predictions
        
        # Storage for predictions
        self.predictions = []
        
    def load_data(self):
        """Load cleaned data files and analysis results"""
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
            self.enrolment_df = pd.read_csv(
                self.data_path / 'enrolment_cleaned.csv',
                parse_dates=['date']
            )
            
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
            
            # Load forecasts if available
            forecast_path = Path('forecast_results')
            if (forecast_path / 'daily_forecasts.csv').exists():
                self.daily_forecasts_df = pd.read_csv(
                    forecast_path / 'daily_forecasts.csv'
                )
                if 'period' in self.daily_forecasts_df.columns:
                    self.daily_forecasts_df['period'] = pd.to_datetime(
                        self.daily_forecasts_df['period'], errors='coerce'
                    )
            else:
                self.daily_forecasts_df = None
            
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
    
    def identify_historical_surges(self, metric='bio_total'):
        """
        Identify historical surge patterns in the data
        
        Args:
            metric: Metric to analyze (bio_total, demo_total, enrol_total)
            
        Returns:
            DataFrame with identified historical surges
        """
        print(f"\nIdentifying historical surges for {metric}...")
        
        # Use daily aggregated data if available
        if self.daily_df is not None and metric in self.daily_df.columns:
            df = self.daily_df[['date', metric]].copy().sort_values('date')
        else:
            # Aggregate from raw data
            if 'bio' in metric:
                df = self.biometric_df.groupby('date').agg({
                    'bio_age_5_17': 'sum',
                    'bio_age_17_': 'sum'
                }).reset_index()
                df[metric] = df['bio_age_5_17'] + df['bio_age_17_']
                df = df[['date', metric]].copy()
            elif 'demo' in metric:
                df = self.demographic_df.groupby('date').agg({
                    'demo_age_5_17': 'sum',
                    'demo_age_17_': 'sum'
                }).reset_index()
                df[metric] = df['demo_age_5_17'] + df['demo_age_17_']
                df = df[['date', metric]].copy()
            elif 'enrol' in metric:
                df = self.enrolment_df.groupby('date').agg({
                    'age_0_5': 'sum',
                    'age_5_17': 'sum',
                    'age_18_greater': 'sum'
                }).reset_index()
                df[metric] = df['age_0_5'] + df['age_5_17'] + df['age_18_greater']
                df = df[['date', metric]].copy()
            else:
                return pd.DataFrame()
        
        df = df.sort_values('date').reset_index(drop=True)
        
        # Calculate baseline (median and mean)
        baseline_median = df[metric].median()
        baseline_mean = df[metric].mean()
        baseline_std = df[metric].std()
        
        # Identify surges (values significantly above baseline)
        surge_threshold = baseline_mean + (self.surge_threshold_multiplier * baseline_std)
        
        df['is_surge'] = df[metric] >= surge_threshold
        df['surge_magnitude'] = (df[metric] - baseline_mean) / baseline_mean if baseline_mean > 0 else 0
        df['surge_intensity'] = (df[metric] - baseline_median) / baseline_median if baseline_median > 0 else 0
        
        # Filter to only surge days
        surges_df = df[df['is_surge']].copy()
        surges_df = surges_df.sort_values('surge_magnitude', ascending=False)
        
        print(f"  Found {len(surges_df)} historical surges")
        print(f"  Baseline mean: {baseline_mean:,.0f}")
        print(f"  Surge threshold: {surge_threshold:,.0f}")
        
        return surges_df, baseline_mean, baseline_std
    
    def predict_age_transition_surges(self):
        """
        Predict surges based on age transitions (children turning 5, 18)
        
        Returns:
            List of predicted surges
        """
        print("\nPredicting age transition surges...")
        
        predictions = []
        
        # Get current date (use max date from data)
        if self.daily_df is not None and len(self.daily_df) > 0:
            current_date = self.daily_df['date'].max()
        elif len(self.enrolment_df) > 0:
            current_date = self.enrolment_df['date'].max()
        else:
            current_date = datetime.now()
        
        # Analyze children in 0-5 age group who will need biometric enrollment
        if self.state_df is not None and 'age_0_5' in self.state_df.columns:
            # Calculate total children 0-5 by state
            state_children = self.state_df[['state', 'age_0_5']].copy()
            state_children = state_children[state_children['age_0_5'] > 0]
            
            # Estimate when they will turn 5 (assuming uniform distribution over 5 years)
            # For simplicity, assume 1/5th will turn 5 each year
            for idx, row in state_children.iterrows():
                state = row['state']
                children_0_5 = row['age_0_5']
                
                # Estimate children turning 5 in next year (uniform distribution)
                children_turning_5_per_month = children_0_5 / 60  # 60 months in 5 years
                
                # Predict surge in 6 months (average time for children to turn 5 in next year)
                surge_date = current_date + timedelta(days=180)  # ~6 months
                days_until = (surge_date - current_date).days
                
                # Estimate surge magnitude based on historical patterns
                # Use ratio of children to historical biometric enrollment
                if self.state_df is not None and 'bio_total' in self.state_df.columns:
                    state_bio = self.state_df[self.state_df['state'] == state]['bio_total'].values
                    if len(state_bio) > 0:
                        historical_bio = state_bio[0]
                        # Estimate that X% of children will enroll
                        estimated_surge = children_turning_5_per_month * 12 * 0.3  # 30% conversion rate assumption
                        surge_magnitude = estimated_surge / historical_bio if historical_bio > 0 else 0
                    else:
                        surge_magnitude = 0.2  # Default assumption
                else:
                    surge_magnitude = 0.2
                
                # Confidence based on number of children
                confidence = min(0.9, 0.5 + (children_0_5 / 100000) * 0.4) if children_0_5 > 0 else 0.3
                
                if confidence >= self.min_surge_confidence and days_until <= self.forecast_horizon_days:
                    prediction = {
                        'surge_type': 'age_transition',
                        'subtype': 'children_turning_5',
                        'state': state,
                        'district': None,
                        'predicted_date': surge_date,
                        'days_until_surge': days_until,
                        'expected_magnitude': surge_magnitude,
                        'estimated_volume': children_turning_5_per_month * 12,
                        'confidence': confidence,
                        'affected_population': children_0_5,
                        'metric': 'bio_total'
                    }
                    predictions.append(prediction)
        
        print(f"  Predicted {len(predictions)} age transition surges")
        return predictions
    
    def predict_forecast_based_surges(self):
        """
        Predict surges based on forecasting models
        
        Returns:
            List of predicted surges
        """
        print("\nPredicting surges based on forecasts...")
        
        predictions = []
        
        # Get current date
        if self.daily_df is not None and len(self.daily_df) > 0:
            current_date = self.daily_df['date'].max()
        else:
            current_date = datetime.now()
        
        # Use forecasts if available
        if self.daily_forecasts_df is not None and len(self.daily_forecasts_df) > 0:
            # Get baseline from historical data
            if self.daily_df is not None and 'bio_total' in self.daily_df.columns:
                baseline_mean = self.daily_df['bio_total'].mean()
                baseline_std = self.daily_df['bio_total'].std()
                surge_threshold = baseline_mean + (self.surge_threshold_multiplier * baseline_std)
                
                # Check forecasts for surge conditions
                forecast_surges = self.daily_forecasts_df[
                    (self.daily_forecasts_df['forecast_value'] >= surge_threshold) &
                    (self.daily_forecasts_df['metric'] == 'bio_total')
                ].copy()
                
                for idx, row in forecast_surges.iterrows():
                    forecast_date = row['period']
                    if isinstance(forecast_date, str):
                        forecast_date = pd.to_datetime(forecast_date)
                    
                    days_until = (forecast_date - current_date).days
                    
                    if 0 <= days_until <= self.forecast_horizon_days:
                        surge_magnitude = (row['forecast_value'] - baseline_mean) / baseline_mean if baseline_mean > 0 else 0
                        confidence = 0.7  # Forecast-based confidence
                        
                        prediction = {
                            'surge_type': 'forecast_based',
                            'subtype': 'temporal_forecast',
                            'state': None,
                            'district': None,
                            'predicted_date': forecast_date,
                            'days_until_surge': days_until,
                            'expected_magnitude': surge_magnitude,
                            'estimated_volume': row['forecast_value'],
                            'confidence': confidence,
                            'affected_population': None,
                            'metric': row['metric']
                        }
                        predictions.append(prediction)
        
        print(f"  Predicted {len(predictions)} forecast-based surges")
        return predictions
    
    def predict_regional_surges(self):
        """
        Predict regional surge patterns based on historical state-level data
        
        Returns:
            List of predicted surges
        """
        print("\nPredicting regional surge patterns...")
        
        predictions = []
        
        if self.state_df is None:
            return predictions
        
        # Get current date
        if self.daily_df is not None and len(self.daily_df) > 0:
            current_date = self.daily_df['date'].max()
        else:
            current_date = datetime.now()
        
        # Analyze state-level patterns
        if 'bio_total' in self.state_df.columns and 'state' in self.state_df.columns:
            state_bio = self.state_df[['state', 'bio_total']].copy()
            overall_mean = state_bio['bio_total'].mean()
            overall_std = state_bio['bio_total'].std()
            
            # Identify states with high activity (potential surge states)
            high_activity_threshold = overall_mean + overall_std
            
            high_activity_states = state_bio[state_bio['bio_total'] >= high_activity_threshold].copy()
            
            # Predict continuation of high activity (next 30-60 days)
            for idx, row in high_activity_states.iterrows():
                state = row['state']
                current_volume = row['bio_total']
                
                # Predict surge in next 30-60 days
                surge_date = current_date + timedelta(days=45)  # Average of 30-60 days
                days_until = (surge_date - current_date).days
                
                surge_magnitude = (current_volume - overall_mean) / overall_mean if overall_mean > 0 else 0
                confidence = min(0.8, 0.5 + (surge_magnitude * 0.3))
                
                if confidence >= self.min_surge_confidence:
                    prediction = {
                        'surge_type': 'regional_pattern',
                        'subtype': 'high_activity_state',
                        'state': state,
                        'district': None,
                        'predicted_date': surge_date,
                        'days_until_surge': days_until,
                        'expected_magnitude': surge_magnitude,
                        'estimated_volume': current_volume,
                        'confidence': confidence,
                        'affected_population': None,
                        'metric': 'bio_total'
                    }
                    predictions.append(prediction)
        
        print(f"  Predicted {len(predictions)} regional surges")
        return predictions
    
    def run_all_predictions(self):
        """
        Run all surge prediction methods
        
        Returns:
            DataFrame with all predictions
        """
        print(f"\n{'='*80}")
        print("SURGE PREDICTION SYSTEM")
        print(f"{'='*80}")
        print(f"\nParameters:")
        print(f"  Surge Threshold Multiplier: {self.surge_threshold_multiplier}")
        print(f"  Forecast Horizon: {self.forecast_horizon_days} days")
        print(f"  Min Confidence: {self.min_surge_confidence}")
        
        all_predictions = []
        
        # Age transition surges
        age_predictions = self.predict_age_transition_surges()
        all_predictions.extend(age_predictions)
        
        # Forecast-based surges
        forecast_predictions = self.predict_forecast_based_surges()
        all_predictions.extend(forecast_predictions)
        
        # Regional surges
        regional_predictions = self.predict_regional_surges()
        all_predictions.extend(regional_predictions)
        
        # Convert to DataFrame
        if all_predictions:
            predictions_df = pd.DataFrame(all_predictions)
            predictions_df = predictions_df.sort_values(['days_until_surge', 'confidence'], ascending=[True, False])
            
            # Add priority level based on confidence and magnitude
            predictions_df['priority'] = predictions_df.apply(
                lambda row: 'High' if row['confidence'] >= 0.7 and row['expected_magnitude'] >= 0.3
                else 'Medium' if row['confidence'] >= 0.6 or row['expected_magnitude'] >= 0.2
                else 'Low', axis=1
            )
            
            print(f"\nTotal predictions: {len(predictions_df)}")
            print(f"  High priority: {len(predictions_df[predictions_df['priority'] == 'High'])}")
            print(f"  Medium priority: {len(predictions_df[predictions_df['priority'] == 'Medium'])}")
            print(f"  Low priority: {len(predictions_df[predictions_df['priority'] == 'Low'])}")
        else:
            predictions_df = pd.DataFrame()
        
        return predictions_df
    
    def save_results(self, predictions_df):
        """
        Save surge prediction results to files
        
        Args:
            predictions_df: DataFrame with predictions
        """
        print(f"\n{'='*80}")
        print("SAVING RESULTS")
        print(f"{'='*80}")
        
        if len(predictions_df) > 0:
            # Save all predictions
            output_file = self.output_path / 'surge_predictions.csv'
            predictions_df.to_csv(output_file, index=False)
            print(f"\n[SUCCESS] Saved: {output_file}")
            print(f"   Total predictions: {len(predictions_df)}")
            
            # Save by surge type
            for surge_type in predictions_df['surge_type'].unique():
                type_df = predictions_df[predictions_df['surge_type'] == surge_type]
                type_file = self.output_path / f'surge_predictions_{surge_type}.csv'
                type_df.to_csv(type_file, index=False)
                print(f"[SUCCESS] Saved: {type_file} ({len(type_df)} predictions)")
            
            # Save upcoming surges (next 30 days)
            upcoming_df = predictions_df[predictions_df['days_until_surge'] <= 30].copy()
            if len(upcoming_df) > 0:
                upcoming_file = self.output_path / 'upcoming_surges.csv'
                upcoming_df.to_csv(upcoming_file, index=False)
                print(f"[SUCCESS] Saved: {upcoming_file} ({len(upcoming_df)} upcoming surges)")
            
            # Create summary JSON
            summary = {
                'total_predictions': len(predictions_df),
                'prediction_date': datetime.now().isoformat(),
                'parameters': {
                    'surge_threshold_multiplier': self.surge_threshold_multiplier,
                    'forecast_horizon_days': self.forecast_horizon_days,
                    'min_confidence': self.min_surge_confidence
                },
                'by_surge_type': {},
                'by_priority': {},
                'upcoming_surges_30_days': len(upcoming_df) if len(upcoming_df) > 0 else 0,
                'upcoming_surges_60_days': len(predictions_df[predictions_df['days_until_surge'] <= 60]),
                'upcoming_surges_90_days': len(predictions_df[predictions_df['days_until_surge'] <= 90])
            }
            
            for surge_type in predictions_df['surge_type'].unique():
                summary['by_surge_type'][surge_type] = len(predictions_df[predictions_df['surge_type'] == surge_type])
            
            for priority in predictions_df['priority'].unique():
                summary['by_priority'][priority] = len(predictions_df[predictions_df['priority'] == priority])
            
            # Save summary JSON
            summary_file = self.output_path / 'surge_predictions_summary.json'
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"[SUCCESS] Saved: {summary_file}")
            
        else:
            print("\n[WARNING] No surge predictions generated.")
    
    def run(self):
        """Run the complete surge prediction pipeline"""
        if not self.load_data():
            return False
        
        predictions_df = self.run_all_predictions()
        self.save_results(predictions_df)
        
        print(f"\n{'='*80}")
        print("[SUCCESS] Surge Prediction System Completed!")
        print(f"{'='*80}")
        
        return True


if __name__ == "__main__":
    predictor = SurgePredictor()
    predictor.run()
