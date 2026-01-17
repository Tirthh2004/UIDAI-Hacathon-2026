"""
Advanced Anomaly Detection Module
AI-Driven Early Warning System for Aadhaar Update Surges

This module implements advanced anomaly detection using:
- IQR Method (Interquartile Range) - Primary method
- MAD Z-Score (Median Absolute Deviation) - Secondary method
- Rolling window detection
- Multi-level detection (temporal + geographic)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import json
from datetime import datetime
warnings.filterwarnings('ignore')


class AdvancedAnomalyDetector:
    """
    Advanced Anomaly Detection using IQR and MAD Z-Score methods
    
    Capability: Anomaly Detection
    Algorithms: IQR Method, MAD Z-Score
    Detection Levels: Temporal, Geographic, Age Group, Ratio
    """
    
    def __init__(self, data_path='processed_data', output_path='anomaly_results'):
        """
        Initialize the Advanced Anomaly Detector
        
        Args:
            data_path: Path to processed data directory
            output_path: Path to save anomaly detection results
        """
        self.data_path = Path(data_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(exist_ok=True)
        
        # Detection parameters
        self.iqr_multiplier = 1.5  # Standard IQR multiplier (1.5, 2.0, or 3.0)
        self.mad_threshold = 3.0   # MAD Z-score threshold
        self.rolling_window = 30   # Rolling window size for temporal detection
        
        # Storage for anomalies
        self.anomalies = []
        
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
    
    def calculate_mad(self, values):
        """
        Calculate Median Absolute Deviation (MAD)
        
        Args:
            values: Array-like of values
            
        Returns:
            MAD value
        """
        median = np.median(values)
        mad = np.median(np.abs(values - median))
        return mad if mad > 0 else 1.0  # Avoid division by zero
    
    def calculate_mad_z_score(self, value, values):
        """
        Calculate MAD-based Z-score (more robust than standard Z-score)
        
        Formula: Modified Z = 0.6745 × (X - median) / MAD
        
        Args:
            value: Current value to score
            values: Array-like of baseline values
            
        Returns:
            MAD Z-score
        """
        median = np.median(values)
        mad = self.calculate_mad(values)
        if mad == 0:
            return 0.0
        modified_z = 0.6745 * (value - median) / mad
        return modified_z
    
    def detect_iqr_anomaly(self, value, values, multiplier=None):
        """
        Detect anomaly using IQR (Interquartile Range) method
        
        Formula:
        - IQR = Q3 - Q1
        - Lower Bound = Q1 - multiplier × IQR
        - Upper Bound = Q3 + multiplier × IQR
        
        Args:
            value: Current value to check
            values: Array-like of baseline values
            multiplier: IQR multiplier (default: self.iqr_multiplier)
            
        Returns:
            tuple: (is_anomaly, lower_bound, upper_bound, deviation)
        """
        if multiplier is None:
            multiplier = self.iqr_multiplier
        
        if len(values) < 4:
            return False, None, None, 0.0
        
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        if iqr == 0:
            # If IQR is 0, use a simple threshold based on median
            median = np.median(values)
            std = np.std(values)
            if std == 0:
                return False, None, None, 0.0
            lower_bound = median - multiplier * std
            upper_bound = median + multiplier * std
        else:
            lower_bound = q1 - multiplier * iqr
            upper_bound = q3 + multiplier * iqr
        
        is_anomaly = (value < lower_bound) or (value > upper_bound)
        
        # Calculate deviation (how many IQRs away)
        if value < lower_bound:
            deviation = (lower_bound - value) / iqr if iqr > 0 else 0.0
        elif value > upper_bound:
            deviation = (value - upper_bound) / iqr if iqr > 0 else float('inf')
        else:
            deviation = 0.0
        
        return is_anomaly, lower_bound, upper_bound, deviation
    
    def detect_temporal_anomalies(self, metric='bio_total', rolling_window=None):
        """
        Detect temporal anomalies using rolling windows
        
        Args:
            metric: Metric to analyze (bio_total, demo_total, enrol_total)
            rolling_window: Rolling window size (default: self.rolling_window)
            
        Returns:
            DataFrame with detected anomalies
        """
        if rolling_window is None:
            rolling_window = self.rolling_window
        
        print(f"\nDetecting temporal anomalies for {metric}...")
        
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
        
        anomalies_list = []
        
        for idx, row in df.iterrows():
            date_val = row['date']
            value = row[metric]
            
            # Get rolling window data (previous values)
            if idx < rolling_window:
                window_data = df.iloc[:idx][metric].values
            else:
                window_data = df.iloc[idx-rolling_window:idx][metric].values
            
            if len(window_data) < 4:
                continue
            
            # IQR detection
            iqr_anomaly, lower_bound, upper_bound, iqr_deviation = self.detect_iqr_anomaly(
                value, window_data
            )
            
            # MAD Z-score detection
            mad_z_score = self.calculate_mad_z_score(value, window_data)
            mad_anomaly = abs(mad_z_score) > self.mad_threshold
            
            # Calculate severity (0-1 scale)
            severity = 0.0
            if iqr_anomaly or mad_anomaly:
                if mad_z_score > 0:
                    severity = min(1.0, abs(mad_z_score) / self.mad_threshold)
                else:
                    severity = min(1.0, iqr_deviation / 2.0) if iqr_deviation > 0 else 0.5
            
            anomaly_record = {
                'detection_level': 'temporal',
                'metric': metric,
                'date': date_val,
                'value': value,
                'iqr_anomaly': iqr_anomaly,
                'mad_anomaly': mad_anomaly,
                'iqr_deviation': iqr_deviation if iqr_deviation != float('inf') else 999.0,
                'mad_z_score': mad_z_score,
                'severity': severity,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'state': None
            }
            
            if iqr_anomaly or mad_anomaly:
                anomalies_list.append(anomaly_record)
                self.anomalies.append(anomaly_record)
        
        anomalies_df = pd.DataFrame(anomalies_list)
        print(f"  Found {len(anomalies_df)} temporal anomalies for {metric}")
        
        return anomalies_df
    
    def detect_geographic_anomalies(self, metric='bio_total', level='state'):
        """
        Detect geographic anomalies at state or district level
        
        Args:
            metric: Metric to analyze (bio_total, demo_total, enrol_total)
            level: Geographic level ('state' or 'district')
            
        Returns:
            DataFrame with detected anomalies
        """
        print(f"\nDetecting {level}-level geographic anomalies for {metric}...")
        
        # Aggregate data by geographic level
        if 'bio' in metric:
            df = self.biometric_df.copy()
            if 'bio_total' not in df.columns:
                df['bio_total'] = df['bio_age_5_17'] + df['bio_age_17_']
            geo_df = df.groupby(level).agg({metric: 'sum'}).reset_index()
        elif 'demo' in metric:
            df = self.demographic_df.copy()
            if 'demo_total' not in df.columns:
                df['demo_total'] = df['demo_age_5_17'] + df['demo_age_17_']
            geo_df = df.groupby(level).agg({metric: 'sum'}).reset_index()
        elif 'enrol' in metric:
            df = self.enrolment_df.copy()
            if 'enrol_total' not in df.columns:
                df['enrol_total'] = df['age_0_5'] + df['age_5_17'] + df['age_18_greater']
            geo_df = df.groupby(level).agg({metric: 'sum'}).reset_index()
        else:
            return pd.DataFrame()
        
        values = geo_df[metric].values
        
        anomalies_list = []
        
        for idx, row in geo_df.iterrows():
            geo_name = row[level]
            value = row[metric]
            
            # Compare against all other geographic units
            other_values = geo_df[geo_df[level] != geo_name][metric].values
            
            if len(other_values) < 4:
                continue
            
            # IQR detection
            iqr_anomaly, lower_bound, upper_bound, iqr_deviation = self.detect_iqr_anomaly(
                value, other_values
            )
            
            # MAD Z-score detection
            mad_z_score = self.calculate_mad_z_score(value, other_values)
            mad_anomaly = abs(mad_z_score) > self.mad_threshold
            
            # Calculate severity
            severity = 0.0
            if iqr_anomaly or mad_anomaly:
                if mad_z_score > 0:
                    severity = min(1.0, abs(mad_z_score) / self.mad_threshold)
                else:
                    severity = min(1.0, iqr_deviation / 2.0) if iqr_deviation > 0 else 0.5
            
            # Set detection_level appropriately
            if level == 'state':
                detection_level = 'geographic'
                state_val = geo_name
            else:
                detection_level = f'geographic_{level}'
                state_val = None
            
            anomaly_record = {
                'detection_level': detection_level,
                'metric': metric,
                'date': None,
                'value': value,
                'iqr_anomaly': iqr_anomaly,
                'mad_anomaly': mad_anomaly,
                'iqr_deviation': iqr_deviation if iqr_deviation != float('inf') else 999.0,
                'mad_z_score': mad_z_score,
                'severity': severity,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'state': state_val
            }
            
            if iqr_anomaly or mad_anomaly:
                anomalies_list.append(anomaly_record)
                self.anomalies.append(anomaly_record)
        
        anomalies_df = pd.DataFrame(anomalies_list)
        print(f"  Found {len(anomalies_df)} {level}-level anomalies for {metric}")
        
        return anomalies_df
    
    def detect_age_group_anomalies(self):
        """
        Detect anomalies in age group distributions
        
        Returns:
            DataFrame with detected anomalies
        """
        print("\nDetecting age group anomalies...")
        
        anomalies_list = []
        
        # Biometric age groups
        bio_age_5_17 = self.biometric_df.groupby('date')['bio_age_5_17'].sum()
        bio_age_17_ = self.biometric_df.groupby('date')['bio_age_17_'].sum()
        bio_total = bio_age_5_17 + bio_age_17_
        
        # Calculate ratios
        bio_ratio_5_17 = (bio_age_5_17 / bio_total).replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Detect anomalies in ratios using rolling window
        ratio_df = pd.DataFrame({
            'date': bio_ratio_5_17.index,
            'ratio': bio_ratio_5_17.values
        }).sort_values('date')
        
        for idx, row in ratio_df.iterrows():
            if idx < self.rolling_window:
                window_data = ratio_df.iloc[:idx]['ratio'].values
            else:
                window_data = ratio_df.iloc[idx-self.rolling_window:idx]['ratio'].values
            
            if len(window_data) < 4:
                continue
            
            value = row['ratio']
            iqr_anomaly, lower_bound, upper_bound, iqr_deviation = self.detect_iqr_anomaly(value, window_data)
            mad_z_score = self.calculate_mad_z_score(value, window_data)
            mad_anomaly = abs(mad_z_score) > self.mad_threshold
            
            severity = 0.0
            if iqr_anomaly or mad_anomaly:
                severity = min(1.0, abs(mad_z_score) / self.mad_threshold) if mad_z_score != 0 else 0.5
            
            if iqr_anomaly or mad_anomaly:
                anomaly_record = {
                    'detection_level': 'age_group',
                    'metric': 'bio_age_ratio_5_17',
                    'date': row['date'],
                    'value': value,
                    'iqr_anomaly': iqr_anomaly,
                    'mad_anomaly': mad_anomaly,
                    'iqr_deviation': iqr_deviation if iqr_deviation != float('inf') else 999.0,
                    'mad_z_score': mad_z_score,
                    'severity': severity,
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound,
                    'state': None
                }
                anomalies_list.append(anomaly_record)
                self.anomalies.append(anomaly_record)
        
        anomalies_df = pd.DataFrame(anomalies_list)
        print(f"  Found {len(anomalies_df)} age group anomalies")
        
        return anomalies_df
    
    def detect_ratio_anomalies(self):
        """
        Detect anomalies in biometric/demographic ratios
        
        Returns:
            DataFrame with detected anomalies
        """
        print("\nDetecting ratio anomalies (biometric/demographic)...")
        
        anomalies_list = []
        
        # Aggregate by date
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
        
        # Merge and calculate ratio
        ratio_df = bio_daily[['date', 'bio_total']].merge(
            demo_daily[['date', 'demo_total']], on='date', how='outer'
        ).fillna(0)
        ratio_df['ratio'] = ratio_df['bio_total'] / (ratio_df['demo_total'] + 1)  # +1 to avoid division by zero
        ratio_df = ratio_df.sort_values('date').reset_index(drop=True)
        
        for idx, row in ratio_df.iterrows():
            if idx < self.rolling_window:
                window_data = ratio_df.iloc[:idx]['ratio'].values
            else:
                window_data = ratio_df.iloc[idx-self.rolling_window:idx]['ratio'].values
            
            if len(window_data) < 4:
                continue
            
            value = row['ratio']
            iqr_anomaly, lower_bound, upper_bound, iqr_deviation = self.detect_iqr_anomaly(value, window_data)
            mad_z_score = self.calculate_mad_z_score(value, window_data)
            mad_anomaly = abs(mad_z_score) > self.mad_threshold
            
            severity = 0.0
            if iqr_anomaly or mad_anomaly:
                severity = min(1.0, abs(mad_z_score) / self.mad_threshold) if mad_z_score != 0 else 0.5
            
            if iqr_anomaly or mad_anomaly:
                anomaly_record = {
                    'detection_level': 'ratio',
                    'metric': 'bio_demo_ratio',
                    'date': row['date'],
                    'value': value,
                    'iqr_anomaly': iqr_anomaly,
                    'mad_anomaly': mad_anomaly,
                    'iqr_deviation': iqr_deviation if iqr_deviation != float('inf') else 999.0,
                    'mad_z_score': mad_z_score,
                    'severity': severity,
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound,
                    'state': None
                }
                anomalies_list.append(anomaly_record)
                self.anomalies.append(anomaly_record)
        
        anomalies_df = pd.DataFrame(anomalies_list)
        print(f"  Found {len(anomalies_df)} ratio anomalies")
        
        return anomalies_df
    
    def run_all_detections(self):
        """
        Run all anomaly detection methods
        
        Returns:
            Dictionary with all detected anomalies
        """
        print(f"\n{'='*80}")
        print("ADVANCED ANOMALY DETECTION")
        print(f"{'='*80}")
        print(f"\nParameters:")
        print(f"  IQR Multiplier: {self.iqr_multiplier}")
        print(f"  MAD Threshold: {self.mad_threshold}")
        print(f"  Rolling Window: {self.rolling_window} days")
        
        all_anomalies = {}
        
        # Temporal anomalies
        metrics = ['bio_total', 'demo_total', 'enrol_total']
        temporal_anomalies_list = []
        for metric in metrics:
            anomalies_df = self.detect_temporal_anomalies(metric)
            if len(anomalies_df) > 0:
                temporal_anomalies_list.append(anomalies_df)
        if temporal_anomalies_list:
            all_anomalies['temporal'] = pd.concat(temporal_anomalies_list, ignore_index=True)
        
        # Geographic anomalies (state level)
        geo_anomalies_list = []
        for metric in metrics:
            anomalies_df = self.detect_geographic_anomalies(metric, level='state')
            if len(anomalies_df) > 0:
                geo_anomalies_list.append(anomalies_df)
        if geo_anomalies_list:
            all_anomalies['geographic'] = pd.concat(geo_anomalies_list, ignore_index=True)
        
        # Age group anomalies
        age_anomalies = self.detect_age_group_anomalies()
        if len(age_anomalies) > 0:
            all_anomalies['age_group'] = age_anomalies
        
        # Ratio anomalies
        ratio_anomalies = self.detect_ratio_anomalies()
        if len(ratio_anomalies) > 0:
            all_anomalies['ratio'] = ratio_anomalies
        
        return all_anomalies
    
    def save_results(self, all_anomalies):
        """
        Save anomaly detection results to files
        
        Args:
            all_anomalies: Dictionary with detected anomalies
        """
        print(f"\n{'='*80}")
        print("SAVING RESULTS")
        print(f"{'='*80}")
        
        # Combine all anomalies
        all_anomalies_list = []
        for key, df in all_anomalies.items():
            all_anomalies_list.append(df)
        
        if all_anomalies_list:
            combined_df = pd.concat(all_anomalies_list, ignore_index=True)
            
            # Save combined anomalies
            output_file = self.output_path / 'anomalies_detected.csv'
            combined_df.to_csv(output_file, index=False)
            print(f"\n[SUCCESS] Saved: {output_file}")
            print(f"   Total anomalies detected: {len(combined_df)}")
            
            # Save by detection level
            if 'temporal' in all_anomalies:
                temporal_file = self.output_path / 'anomalies_temporal.csv'
                all_anomalies['temporal'].to_csv(temporal_file, index=False)
                print(f"[SUCCESS] Saved: {temporal_file} ({len(all_anomalies['temporal'])} anomalies)")
            
            if 'geographic' in all_anomalies:
                geo_file = self.output_path / 'anomalies_geographic.csv'
                all_anomalies['geographic'].to_csv(geo_file, index=False)
                print(f"[SUCCESS] Saved: {geo_file} ({len(all_anomalies['geographic'])} anomalies)")
            
            if 'age_group' in all_anomalies:
                age_file = self.output_path / 'anomalies_age_group.csv'
                all_anomalies['age_group'].to_csv(age_file, index=False)
                print(f"[SUCCESS] Saved: {age_file} ({len(all_anomalies['age_group'])} anomalies)")
            
            if 'ratio' in all_anomalies:
                ratio_file = self.output_path / 'anomalies_ratio.csv'
                all_anomalies['ratio'].to_csv(ratio_file, index=False)
                print(f"[SUCCESS] Saved: {ratio_file} ({len(all_anomalies['ratio'])} anomalies)")
            
            # Create summary statistics
            summary = {
                'total_anomalies': len(combined_df),
                'detection_date': datetime.now().isoformat(),
                'parameters': {
                    'iqr_multiplier': self.iqr_multiplier,
                    'mad_threshold': self.mad_threshold,
                    'rolling_window': self.rolling_window
                },
                'by_detection_level': {},
                'by_metric': {},
                'severity_distribution': {
                    'high': len(combined_df[combined_df['severity'] >= 0.8]),
                    'medium': len(combined_df[(combined_df['severity'] >= 0.5) & (combined_df['severity'] < 0.8)]),
                    'low': len(combined_df[combined_df['severity'] < 0.5])
                }
            }
            
            for level in combined_df['detection_level'].unique():
                summary['by_detection_level'][level] = len(combined_df[combined_df['detection_level'] == level])
            
            for metric in combined_df['metric'].unique():
                summary['by_metric'][metric] = len(combined_df[combined_df['metric'] == metric])
            
            # Save summary JSON
            summary_file = self.output_path / 'anomalies_summary.json'
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"[SUCCESS] Saved: {summary_file}")
            
            # Save summary CSV
            summary_df = pd.DataFrame([summary])
            summary_csv = self.output_path / 'anomalies_summary.csv'
            summary_df.to_csv(summary_csv, index=False)
            print(f"[SUCCESS] Saved: {summary_csv}")
            
        else:
            print("\n[WARNING] No anomalies detected.")
    
    def run(self):
        """Run the complete anomaly detection pipeline"""
        if not self.load_data():
            return False
        
        all_anomalies = self.run_all_detections()
        self.save_results(all_anomalies)
        
        print(f"\n{'='*80}")
        print("[SUCCESS] Advanced Anomaly Detection Completed!")
        print(f"{'='*80}")
        
        return True


if __name__ == "__main__":
    detector = AdvancedAnomalyDetector()
    detector.run()
