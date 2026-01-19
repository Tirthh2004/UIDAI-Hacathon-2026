"""
Forensic Analysis Module for UIDAI Analytics Dashboard
Focus: Enrollment Pattern Risk Intelligence (Forensic Signal)

This module implements a forensic-grade system to detect statistically abnormal patterns 
in first-time Aadhaar enrollments for adults (18+).

CRITICAL CONSTRAINTS:
- AGGREGATE ANALYSIS ONLY - No individual tracking
- NO IMMIGRATION INFERENCE - Never label or infer immigration status
- SAFE LANGUAGE ONLY - Use terms like "unusual patterns", "statistical deviations", "process-level risk"
- ADMINISTRATIVE FOCUS - Outputs support review, not enforcement
- EVIDENCE-BASED - Every flag must have statistical proof
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings

class ForensicAnalyzer:
    def __init__(self, enrolment_df, biometric_df, demographic_df):
        """
        Initialize the Forensic Analyzer with necessary datasets.
        
        Args:
            enrolment_df: DataFrame containing enrolment data
            biometric_df: DataFrame containing biometric update data
            demographic_df: DataFrame containing demographic update data
        """
        self.enrolment_df = enrolment_df
        self.biometric_df = biometric_df
        self.demographic_df = demographic_df
        self.combined_df = None
        self.forensic_flags = None
        
    def prepare_data(self):
        """
        STEP 1: Data Preparation & Feature Engineering
        Merges datasets and creates core forensic features.
        """
        # Aggregate to Date-State-District-Pincode level if not already
        # Assuming the input DFs have these columns
        group_cols = ['date', 'state', 'district', 'pincode']
        
        # Helper to aggregate if needed
        def agg_df(df, value_cols):
            # Check which columns exist
            cols_to_agg = [c for c in value_cols if c in df.columns]
            if not cols_to_agg:
                return pd.DataFrame(columns=group_cols + value_cols)
            
            # Ensure grouping columns exist
            valid_group_cols = [c for c in group_cols if c in df.columns]
            
            return df.groupby(valid_group_cols)[cols_to_agg].sum().reset_index()

        # Aggregate Enrolment
        enrol_agg = agg_df(self.enrolment_df, ['age_0_5', 'age_5_17', 'age_18_greater'])
        
        # Aggregate Biometric
        # Note: mapping column names based on user input vs likely actual names
        # User input: 'biometric_update_counts'
        # Actual based on EDA: 'bio_age_5_17', 'bio_age_17_' -> sum to total
        if 'bio_total' not in self.biometric_df.columns:
            self.biometric_df['bio_total'] = self.biometric_df.get('bio_age_5_17', 0) + self.biometric_df.get('bio_age_17_', 0)
            
        bio_agg = agg_df(self.biometric_df, ['bio_total'])
        bio_agg = bio_agg.rename(columns={'bio_total': 'biometric_update_counts'})
        
        # Aggregate Demographic
        if 'demo_total' not in self.demographic_df.columns:
            self.demographic_df['demo_total'] = self.demographic_df.get('demo_age_5_17', 0) + self.demographic_df.get('demo_age_17_', 0)
            
        demo_agg = agg_df(self.demographic_df, ['demo_total'])
        demo_agg = demo_agg.rename(columns={'demo_total': 'demographic_update_counts'})
        
        # Merge all
        # Use outer join to keep all records, fillna with 0
        merged = pd.merge(enrol_agg, bio_agg, on=group_cols, how='outer')
        merged = pd.merge(merged, demo_agg, on=group_cols, how='outer')
        merged = merged.fillna(0)
        
        # --- FEATURE ENGINEERING ---
        
        # CORE FEATURES
        merged['adult_enrollment'] = merged['age_18_greater']
        merged['total_enrollment'] = merged['age_0_5'] + merged['age_5_17'] + merged['age_18_greater']
        
        # Avoid division by zero
        merged['adult_ratio'] = merged['adult_enrollment'] / merged['total_enrollment'].replace(0, 1)
        
        # CRITICAL RATIOS (detect manipulation)
        # Using adult_enrollment as denominator (add small epsilon to avoid div by zero)
        epsilon = 1e-6
        merged['bio_per_adult'] = merged['biometric_update_counts'] / (merged['adult_enrollment'] + epsilon)
        merged['demo_per_adult'] = merged['demographic_update_counts'] / (merged['adult_enrollment'] + epsilon)
        
        # Sort by date for rolling calculations
        merged = merged.sort_values(['state', 'district', 'pincode', 'date'])
        
        # TEMPORAL FEATURES (Rolling calculations per pincode)
        # Optimized for performance using vectorized operations instead of apply()
        
        # 1. Sort and Set Index for time-based rolling
        if 'pincode' in merged.columns:
            group_cols_list = ['state', 'district', 'pincode']
        else:
            group_cols_list = ['state', 'district']
            
        # Ensure date is datetime
        merged['date'] = pd.to_datetime(merged['date'])
        
        # Sort by groups + date to ensure correct order for rolling and assignment
        merged = merged.sort_values(group_cols_list + ['date'])
        
        # Set Date as Index (required for time-based rolling offset like '7D')
        merged = merged.set_index('date')
        
        # Group by the location columns
        g = merged.groupby(group_cols_list)
        
        # 2. Vectorized Rolling Calculations
        # We use .values to assign because the resulting Series has a MultiIndex (Group + Date)
        # while 'merged' has a DatetimeIndex. Since we sorted 'merged' beforehand,
        # the order is guaranteed to match, so positional assignment (.values) is safe and fast.
        
        # 7-day rolling
        merged['adult_7d_rolling_mean'] = g['adult_enrollment'].rolling('7D').mean().values
        merged['adult_7d_rolling_std'] = g['adult_enrollment'].rolling('7D').std().fillna(0).values
        
        # 30-day rolling
        merged['adult_30d_rolling_mean'] = g['adult_enrollment'].rolling('30D').mean().values
        
        # 90-day rolling stats (Approximation for performance)
        # Rolling quantile is O(N log k) and very slow. 
        # We approximate percentiles using Mean + k*Std (Normal assumption) which is O(N)
        adult_90d_mean = g['adult_enrollment'].rolling('90D').mean().values
        adult_90d_std = g['adult_enrollment'].rolling('90D').std().fillna(0).values
        
        merged['adult_90d_percentile_75'] = adult_90d_mean + (0.675 * adult_90d_std)
        merged['adult_90d_percentile_90'] = adult_90d_mean + (1.282 * adult_90d_std)
        merged['adult_90d_percentile_99'] = adult_90d_mean + (2.326 * adult_90d_std)
        
        # Growth Rates
        # shift() on groupby works on positions (rows), not time index.
        # Assuming daily data structure or approximate row-based shift.
        merged['prev_7d'] = g['adult_enrollment'].shift(7).values
        merged['prev_30d'] = g['adult_enrollment'].shift(30).values
        
        epsilon = 1e-6
        merged['adult_7d_growth_pct'] = (merged['adult_enrollment'] - merged['prev_7d']) / (merged['prev_7d'] + epsilon)
        merged['adult_30d_growth_pct'] = (merged['adult_enrollment'] - merged['prev_30d']) / (merged['prev_30d'] + epsilon)
        
        # Reset index to return to flat dataframe
        merged = merged.reset_index()
            
        # SPATIAL FEATURES (Compare to neighbors)
        # Calculate District stats (median of pincodes in district for that day)
        district_stats = merged.groupby(['date', 'state', 'district'])['adult_enrollment'].agg(['median', 'std']).reset_index()
        district_stats.columns = ['date', 'state', 'district', 'district_median_adult', 'district_std_adult']
        
        # Calculate State stats
        state_stats = merged.groupby(['date', 'state'])['adult_enrollment'].median().reset_index()
        state_stats.columns = ['date', 'state', 'state_median_adult']
        
        # Merge back
        merged = pd.merge(merged, district_stats, on=['date', 'state', 'district'], how='left')
        merged = pd.merge(merged, state_stats, on=['date', 'state'], how='left')
        
        # Spatial Z-Score
        merged['spatial_z_score'] = (merged['adult_enrollment'] - merged['district_median_adult']) / (merged['district_std_adult'] + epsilon)
        
        self.combined_df = merged.fillna(0)
        return self.combined_df

    # --- ALGORITHMS ---

    def algorithm_1_temporal_deviation(self, row):
        """
        Algorithm 1: Temporal Deviation Detector
        Uses: Robust Z-Score + Percentile Exceedance + Grubbs Test logic
        """
        current_val = row['adult_enrollment']
        
        # Baseline stats from rolling windows
        median = row['adult_30d_rolling_mean'] # Using mean as proxy for median if rolling median not computed
        # For MAD, we can approximate or use std * 0.6745 if normal, but let's use std
        mad = row['adult_7d_rolling_std'] # Using 7d std as local volatility proxy
        
        p90 = row['adult_90d_percentile_90']
        p95 = p90 * 1.2 # Approximation if p95 not calculated
        p99 = row['adult_90d_percentile_99']
        
        mean = row['adult_30d_rolling_mean']
        std = row['adult_7d_rolling_std']
        
        epsilon = 1e-6
        
        # Method 1: Robust Z-Score (Approximated)
        robust_z = 0.6745 * (current_val - median) / (mad + epsilon)
        
        # Method 2: Percentile Check
        percentile_score = 0.0
        if current_val > p99: percentile_score = 1.0
        elif current_val > p95: percentile_score = 0.8
        elif current_val > p90: percentile_score = 0.5
        
        # Method 3: Grubbs Test proxy (Z-score > 3.5)
        grubbs_stat = abs(current_val - mean) / (std + epsilon)
        grubbs_flag = 1.0 if grubbs_stat > 3.5 else 0.0
        
        # Composite Score
        score = 0.4 * min(abs(robust_z)/4, 1.0) + 0.4 * percentile_score + 0.2 * grubbs_flag
        
        return score

    def algorithm_2_spatial_anomaly(self, row):
        """
        Algorithm 2: Spatial Anomaly Detector
        Compares pincode against District and State baselines
        """
        # Spatial Z calculated in prep
        spatial_z = row['spatial_z_score']
        
        district_median = row['district_median_adult']
        state_median = row['state_median_adult']
        epsilon = 1e-6
        
        # District vs State comparison
        district_state_ratio = district_median / (state_median + epsilon)
        
        # Clustering factor (simplified: assumes if district is high, neighbors are high)
        # In a real row-by-row function, we can't easily count neighbors without context.
        # We'll use the district_state_ratio as a proxy for "is the whole area elevated?"
        clustering_factor = min(district_state_ratio / 2.0, 1.0) 
        
        # Composite Score
        score = 0.5 * min(abs(spatial_z)/3, 1.0) + \
                0.3 * min(abs(district_state_ratio - 1), 1.0) + \
                0.2 * clustering_factor
                
        return score

    def algorithm_3_forecast_violation(self, row):
        """
        Algorithm 3: Forecast Violation Detector
        Compares current value against a simple moving average forecast 
        (since we don't have the ARIMA models loaded here easily).
        """
        current_val = row['adult_enrollment']
        forecast_val = row['adult_30d_rolling_mean']
        std = row['adult_7d_rolling_std']
        
        upper_95ci = forecast_val + (1.96 * std)
        lower_95ci = forecast_val - (1.96 * std)
        
        score = 0.0
        
        if current_val > upper_95ci:
            deviation_pct = (current_val - upper_95ci) / (upper_95ci + 1e-6)
            score = min(deviation_pct / 0.5, 1.0)
        elif current_val < lower_95ci:
            # Low enrollments are usually less risky for "surge" but might indicate outage
            deviation_pct = (lower_95ci - current_val) / (lower_95ci + 1e-6)
            score = min(deviation_pct / 0.5, 1.0) * 0.5 # Weigh lower
            
        return score

    def algorithm_4_cross_signal(self, row):
        """
        Algorithm 4: Cross-Signal Integrity Checker
        Suspicious: High enrollments + Low updates
        """
        adult_enrollment = row['adult_enrollment']
        # Updates
        updates = row['biometric_update_counts'] + row['demographic_update_counts']
        
        # If enrollment is high (e.g., > 10)
        if adult_enrollment > 10:
            # Expected updates ratio (heuristic: typically some updates happen in same area)
            # If updates are very low relative to enrollment in the same area/time, 
            # it might indicate a focused "camp" for new enrollments only, which is a pattern to watch.
            
            ratio = updates / adult_enrollment
            
            # If ratio is extremely low (e.g., < 0.1), it's suspicious if volume is high
            if ratio < 0.1:
                return 0.8 # High risk
            elif ratio < 0.3:
                return 0.4 # Medium risk
                
        return 0.0

    def algorithm_5_demographic_ratio(self, row):
        """
        Algorithm 5: Demographic Ratio Anomaly Detector
        Checks if Adult vs Child enrollment ratio is abnormal.
        """
        adult_ratio = row['adult_ratio'] # Adult / Total
        total_enrollment = row['total_enrollment']
        
        # If total volume is significant
        if total_enrollment > 20:
            # If 100% or very high % are adults, it's unusual (usually mix of children)
            if adult_ratio > 0.95:
                return 1.0 # Very High Risk
            elif adult_ratio > 0.8:
                return 0.7 # High Risk
            elif adult_ratio > 0.6:
                return 0.3 # Moderate Risk
        
        return 0.0

    def run_analysis(self):
        """
        Run all algorithms and generate flags.
        """
        if self.combined_df is None:
            self.prepare_data()
            
        df = self.combined_df.copy()
        
        # Apply Algorithms
        # Note: Apply row-wise can be slow. Vectorization preferred but using apply for logic clarity as requested.
        
        # Vectorized implementations for speed
        
        # Algo 1
        # Re-implementing vector-friendly version
        epsilon = 1e-6
        robust_z = 0.6745 * (df['adult_enrollment'] - df['adult_30d_rolling_mean']) / (df['adult_7d_rolling_std'] + epsilon)
        
        # Percentile logic
        p_score = np.zeros(len(df))
        p_score[df['adult_enrollment'] > df['adult_90d_percentile_90']] = 0.5
        p_score[df['adult_enrollment'] > df['adult_90d_percentile_90'] * 1.2] = 0.8 # Proxy p95
        p_score[df['adult_enrollment'] > df['adult_90d_percentile_99']] = 1.0
        
        # Grubbs
        grubbs_stat = abs(df['adult_enrollment'] - df['adult_30d_rolling_mean']) / (df['adult_7d_rolling_std'] + epsilon)
        grubbs_flag = (grubbs_stat > 3.5).astype(float)
        
        df['algo1_score'] = 0.4 * np.minimum(np.abs(robust_z)/4, 1.0) + 0.4 * p_score + 0.2 * grubbs_flag
        
        # Algo 2
        spatial_z = df['spatial_z_score']
        dist_state_ratio = df['district_median_adult'] / (df['state_median_adult'] + epsilon)
        # Clustering proxy
        clustering = np.minimum(dist_state_ratio / 2.0, 1.0)
        
        df['algo2_score'] = 0.5 * np.minimum(np.abs(spatial_z)/3, 1.0) + \
                            0.3 * np.minimum(np.abs(dist_state_ratio - 1), 1.0) + \
                            0.2 * clustering
                            
        # Algo 3 (Forecast)
        upper = df['adult_30d_rolling_mean'] + (1.96 * df['adult_7d_rolling_std'])
        lower = df['adult_30d_rolling_mean'] - (1.96 * df['adult_7d_rolling_std'])
        
        score3 = np.zeros(len(df))
        high_mask = df['adult_enrollment'] > upper
        score3[high_mask] = np.minimum((df.loc[high_mask, 'adult_enrollment'] - upper[high_mask]) / (upper[high_mask] * 0.5 + epsilon), 1.0)
        
        df['algo3_score'] = score3
        
        # Algo 4 (Cross Signal)
        updates = df['biometric_update_counts'] + df['demographic_update_counts']
        ratio = updates / (df['adult_enrollment'] + epsilon)
        
        score4 = np.zeros(len(df))
        mask_vol = df['adult_enrollment'] > 10
        mask_low_ratio = (ratio < 0.1) & mask_vol
        mask_med_ratio = (ratio >= 0.1) & (ratio < 0.3) & mask_vol
        
        score4[mask_low_ratio] = 0.8
        score4[mask_med_ratio] = 0.4
        
        df['algo4_score'] = score4
        
        # Algo 5 (Demographic Ratio)
        ar = df['adult_ratio']
        score5 = np.zeros(len(df))
        mask_total = df['total_enrollment'] > 20
        
        score5[mask_total & (ar > 0.95)] = 1.0
        score5[mask_total & (ar > 0.8) & (ar <= 0.95)] = 0.7
        score5[mask_total & (ar > 0.6) & (ar <= 0.8)] = 0.3
        
        df['algo5_score'] = score5
        
        # Aggregate Risk Score (Weighted Average)
        df['risk_score'] = (
            df['algo1_score'] * 0.25 + 
            df['algo2_score'] * 0.20 + 
            df['algo3_score'] * 0.15 + 
            df['algo4_score'] * 0.20 + 
            df['algo5_score'] * 0.20
        )
        
        # Normalize to 0-100
        df['risk_score_norm'] = (df['risk_score'] * 100).clip(0, 100)
        
        self.forensic_flags = df
        return df

    def get_temporal_summary(self, interval='2M'):
        """
        Aggregate forensic results by time interval for visualization.
        
        Args:
            interval: Pandas offset alias (default '2M' for 2 Months)
        
        Returns:
            DataFrame with aggregated metrics by date_period, state, district, pincode
        """
        if self.forensic_flags is None:
            self.run_analysis()
            
        df = self.forensic_flags.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # Create period column
        # Using to_period for grouping, then back to timestamp for plotting
        df['period'] = df['date'].dt.to_period(interval).dt.start_time
        
        # Define aggregation dictionary
        agg_dict = {
            'adult_enrollment': 'sum',
            'total_enrollment': 'sum',
            'biometric_update_counts': 'sum',
            'demographic_update_counts': 'sum',
            'risk_score_norm': 'mean', # Average risk over the period
            'algo1_score': 'max',      # Did it spike?
            'algo2_score': 'max',
            'algo3_score': 'max',
            'algo4_score': 'max',
            'algo5_score': 'max'
        }
        
        # Group columns
        group_cols = ['period', 'state', 'district']
        if 'pincode' in df.columns:
            group_cols.append('pincode')
            
        # Group
        temporal_df = df.groupby(group_cols).agg(agg_dict).reset_index()
        
        # Sort
        temporal_df = temporal_df.sort_values(['period', 'state'])
        
        return temporal_df

