"""
Exploratory Data Analysis (EDA) for UIDAI Hackathon Project
AI-Driven Early Warning System for Aadhaar Update Surges and Anomalies

This script performs comprehensive pattern discovery and analysis on cleaned datasets.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Optional visualization imports
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette("husl")
except ImportError:
    PLOTTING_AVAILABLE = False
    print("Warning: matplotlib/seaborn not available. Analysis will continue without plots.")


class DataExplorer:
    """Comprehensive data exploration and pattern discovery"""
    
    def __init__(self, data_path='processed_data'):
        """
        Initialize the data explorer
        
        Args:
            data_path: Path to directory containing cleaned data files
        """
        self.data_path = Path(data_path)
        self.results_path = Path('analysis_results')
        self.results_path.mkdir(exist_ok=True)
        
        # Load datasets
        print("Loading cleaned datasets...")
        self.biometric_df = pd.read_csv(self.data_path / 'biometric_cleaned.csv', parse_dates=['date'])
        self.demographic_df = pd.read_csv(self.data_path / 'demographic_cleaned.csv', parse_dates=['date'])
        self.enrolment_df = pd.read_csv(self.data_path / 'enrolment_cleaned.csv', parse_dates=['date'])
        
        # Convert date columns if not already datetime
        for df in [self.biometric_df, self.demographic_df, self.enrolment_df]:
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
        
        print(f"  Biometric: {len(self.biometric_df):,} rows")
        print(f"  Demographic: {len(self.demographic_df):,} rows")
        print(f"  Enrolment: {len(self.enrolment_df):,} rows")
        
        # Storage for derived metrics
        self.insights = []
        
    def analyze_temporal_patterns(self):
        """Analyze time-series patterns and trends"""
        print(f"\n{'='*80}")
        print("TEMPORAL PATTERN ANALYSIS")
        print(f"{'='*80}")
        
        results = {}
        
        # 1. Daily aggregations
        print("\n1. Daily Trends Analysis")
        print("-" * 80)
        
        # Biometric daily totals
        bio_daily = self.biometric_df.groupby('date').agg({
            'bio_age_5_17': 'sum',
            'bio_age_17_': 'sum'
        }).reset_index()
        bio_daily['bio_total'] = bio_daily['bio_age_5_17'] + bio_daily['bio_age_17_']
        
        # Demographic daily totals
        demo_daily = self.demographic_df.groupby('date').agg({
            'demo_age_5_17': 'sum',
            'demo_age_17_': 'sum'
        }).reset_index()
        demo_daily['demo_total'] = demo_daily['demo_age_5_17'] + demo_daily['demo_age_17_']
        
        # Enrolment daily totals
        enrol_daily = self.enrolment_df.groupby('date').agg({
            'age_0_5': 'sum',
            'age_5_17': 'sum',
            'age_18_greater': 'sum'
        }).reset_index()
        enrol_daily['enrol_total'] = enrol_daily['age_0_5'] + enrol_daily['age_5_17'] + enrol_daily['age_18_greater']
        
        # Merge all daily data
        daily_df = bio_daily.merge(demo_daily, on='date', how='outer').merge(enrol_daily, on='date', how='outer')
        daily_df = daily_df.sort_values('date').fillna(0)
        
        # Calculate statistics
        print(f"  Date range: {daily_df['date'].min().date()} to {daily_df['date'].max().date()}")
        print(f"  Total days: {len(daily_df)}")
        
        print(f"\n  Daily Statistics (Averages):")
        print(f"    Biometric updates: {daily_df['bio_total'].mean():,.0f} (std: {daily_df['bio_total'].std():,.0f})")
        print(f"    Demographic updates: {daily_df['demo_total'].mean():,.0f} (std: {daily_df['demo_total'].std():,.0f})")
        print(f"    Enrolments: {daily_df['enrol_total'].mean():,.0f} (std: {daily_df['enrol_total'].std():,.0f})")
        
        # Peak days
        bio_peak = daily_df.loc[daily_df['bio_total'].idxmax()]
        demo_peak = daily_df.loc[daily_df['demo_total'].idxmax()]
        enrol_peak = daily_df.loc[daily_df['enrol_total'].idxmax()]
        
        print(f"\n  Peak Days:")
        print(f"    Biometric: {bio_peak['date'].date()} ({bio_peak['bio_total']:,.0f} updates)")
        print(f"    Demographic: {demo_peak['date'].date()} ({demo_peak['demo_total']:,.0f} updates)")
        print(f"    Enrolment: {enrol_peak['date'].date()} ({enrol_peak['enrol_total']:,.0f} enrolments)")
        
        # 2. Weekly patterns
        print("\n2. Weekly Pattern Analysis")
        print("-" * 80)
        daily_df['weekday'] = daily_df['date'].dt.day_name()
        daily_df['week'] = daily_df['date'].dt.isocalendar().week
        daily_df['month'] = daily_df['date'].dt.month
        
        weekday_avg = daily_df.groupby('weekday')[['bio_total', 'demo_total', 'enrol_total']].mean()
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_avg = weekday_avg.reindex([d for d in weekday_order if d in weekday_avg.index])
        
        print("\n  Average by Day of Week:")
        for day in weekday_avg.index:
            print(f"    {day:12}: Bio={weekday_avg.loc[day, 'bio_total']:7,.0f}, "
                  f"Demo={weekday_avg.loc[day, 'demo_total']:7,.0f}, "
                  f"Enrol={weekday_avg.loc[day, 'enrol_total']:7,.0f}")
        
        # 3. Monthly trends
        print("\n3. Monthly Trend Analysis")
        print("-" * 80)
        monthly_avg = daily_df.groupby('month')[['bio_total', 'demo_total', 'enrol_total']].mean()
        month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                      7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
        
        print("\n  Average by Month:")
        for month in sorted(monthly_avg.index):
            month_name = month_names.get(month, f'M{month}')
            print(f"    {month_name:4}: Bio={monthly_avg.loc[month, 'bio_total']:7,.0f}, "
                  f"Demo={monthly_avg.loc[month, 'demo_total']:7,.0f}, "
                  f"Enrol={monthly_avg.loc[month, 'enrol_total']:7,.0f}")
        
        # 4. Trend direction (simple linear trend)
        print("\n4. Overall Trend Direction")
        print("-" * 80)
        daily_df['day_num'] = (daily_df['date'] - daily_df['date'].min()).dt.days
        
        for metric in ['bio_total', 'demo_total', 'enrol_total']:
            slope = np.polyfit(daily_df['day_num'], daily_df[metric], 1)[0]
            trend = "Increasing" if slope > 0 else "Decreasing"
            print(f"  {metric.replace('_', ' ').title()}: {trend} trend "
                  f"(slope: {slope:,.2f} per day)")
        
        results['daily_df'] = daily_df
        results['weekday_avg'] = weekday_avg
        results['monthly_avg'] = monthly_avg
        
        return results
    
    def analyze_geographic_patterns(self):
        """Analyze geographic distribution patterns"""
        print(f"\n{'='*80}")
        print("GEOGRAPHIC PATTERN ANALYSIS")
        print(f"{'='*80}")
        
        results = {}
        
        # 1. State-level analysis
        print("\n1. State-Level Analysis")
        print("-" * 80)
        
        # Biometric by state
        bio_state = self.biometric_df.groupby('state').agg({
            'bio_age_5_17': 'sum',
            'bio_age_17_': 'sum',
            'pincode': 'nunique',
            'district': 'nunique'
        }).reset_index()
        bio_state['bio_total'] = bio_state['bio_age_5_17'] + bio_state['bio_age_17_']
        bio_state = bio_state.sort_values('bio_total', ascending=False)
        
        # Demographic by state
        demo_state = self.demographic_df.groupby('state').agg({
            'demo_age_5_17': 'sum',
            'demo_age_17_': 'sum'
        }).reset_index()
        demo_state['demo_total'] = demo_state['demo_age_5_17'] + demo_state['demo_age_17_']
        
        # Enrolment by state
        enrol_state = self.enrolment_df.groupby('state').agg({
            'age_0_5': 'sum',
            'age_5_17': 'sum',
            'age_18_greater': 'sum'
        }).reset_index()
        enrol_state['enrol_total'] = enrol_state['age_0_5'] + enrol_state['age_5_17'] + enrol_state['age_18_greater']
        
        # Merge state data
        state_df = bio_state.merge(demo_state, on='state', how='outer').merge(enrol_state, on='state', how='outer')
        state_df = state_df.fillna(0).sort_values('bio_total', ascending=False)
        
        print(f"  Total states: {len(state_df)}")
        print(f"\n  Top 10 States by Biometric Updates:")
        for idx, row in state_df.head(10).iterrows():
            print(f"    {row['state']:25}: {row['bio_total']:10,.0f} updates "
                  f"(Districts: {row['district']:3.0f}, Pincodes: {row['pincode']:5.0f})")
        
        print(f"\n  Top 10 States by Demographic Updates:")
        demo_top = state_df.sort_values('demo_total', ascending=False).head(10)
        for idx, row in demo_top.iterrows():
            print(f"    {row['state']:25}: {row['demo_total']:10,.0f} updates")
        
        print(f"\n  Top 10 States by Enrolments:")
        enrol_top = state_df.sort_values('enrol_total', ascending=False).head(10)
        for idx, row in enrol_top.iterrows():
            print(f"    {row['state']:25}: {row['enrol_total']:10,.0f} enrolments")
        
        # 2. District-level analysis
        print("\n2. District-Level Analysis")
        print("-" * 80)
        
        bio_district = self.biometric_df.groupby(['state', 'district']).agg({
            'bio_age_5_17': 'sum',
            'bio_age_17_': 'sum',
            'pincode': 'nunique'
        }).reset_index()
        bio_district['bio_total'] = bio_district['bio_age_5_17'] + bio_district['bio_age_17_']
        bio_district = bio_district.sort_values('bio_total', ascending=False)
        
        print(f"  Total districts: {bio_district['district'].nunique()}")
        print(f"\n  Top 10 Districts by Biometric Updates:")
        for idx, row in bio_district.head(10).iterrows():
            print(f"    {row['state']:20} - {row['district']:20}: {row['bio_total']:10,.0f} "
                  f"(Pincodes: {row['pincode']:3.0f})")
        
        # 3. Geographic coverage statistics
        print("\n3. Geographic Coverage Statistics")
        print("-" * 80)
        print(f"  Unique States: {self.biometric_df['state'].nunique()}")
        print(f"  Unique Districts: {self.biometric_df['district'].nunique()}")
        print(f"  Unique Pincodes: {self.biometric_df['pincode'].nunique()}")
        
        # Pincode distribution
        pincode_counts = self.biometric_df.groupby('pincode').size()
        print(f"\n  Pincode Activity:")
        print(f"    Pincodes with data: {len(pincode_counts):,}")
        print(f"    Average records per pincode: {pincode_counts.mean():.1f}")
        print(f"    Max records per pincode: {pincode_counts.max():,}")
        print(f"    Pincodes with >100 records: {(pincode_counts > 100).sum():,}")
        
        results['state_df'] = state_df
        results['bio_district'] = bio_district
        results['pincode_counts'] = pincode_counts
        
        return results
    
    def analyze_age_patterns(self):
        """Analyze age group patterns and transitions"""
        print(f"\n{'='*80}")
        print("AGE GROUP PATTERN ANALYSIS")
        print(f"{'='*80}")
        
        results = {}
        
        # 1. Age group distributions
        print("\n1. Age Group Distribution Analysis")
        print("-" * 80)
        
        # Biometric age groups
        bio_age_totals = {
            '5-17': self.biometric_df['bio_age_5_17'].sum(),
            '17+': self.biometric_df['bio_age_17_'].sum()
        }
        bio_total = sum(bio_age_totals.values())
        
        # Demographic age groups
        demo_age_totals = {
            '5-17': self.demographic_df['demo_age_5_17'].sum(),
            '17+': self.demographic_df['demo_age_17_'].sum()
        }
        demo_total = sum(demo_age_totals.values())
        
        # Enrolment age groups
        enrol_age_totals = {
            '0-5': self.enrolment_df['age_0_5'].sum(),
            '5-17': self.enrolment_df['age_5_17'].sum(),
            '18+': self.enrolment_df['age_18_greater'].sum()
        }
        enrol_total = sum(enrol_age_totals.values())
        
        print(f"  Biometric Updates by Age Group:")
        for age, count in bio_age_totals.items():
            pct = (count / bio_total * 100) if bio_total > 0 else 0
            print(f"    Age {age:4}: {count:12,.0f} ({pct:5.2f}%)")
        
        print(f"\n  Demographic Updates by Age Group:")
        for age, count in demo_age_totals.items():
            pct = (count / demo_total * 100) if demo_total > 0 else 0
            print(f"    Age {age:4}: {count:12,.0f} ({pct:5.2f}%)")
        
        print(f"\n  Enrolments by Age Group:")
        for age, count in enrol_age_totals.items():
            pct = (count / enrol_total * 100) if enrol_total > 0 else 0
            print(f"    Age {age:4}: {count:12,.0f} ({pct:5.2f}%)")
        
        # 2. Age transition analysis (5-17 to 17+)
        print("\n2. Age Transition Analysis")
        print("-" * 80)
        
        # Calculate ratios
        bio_ratio = self.biometric_df['bio_age_17_'].sum() / self.biometric_df['bio_age_5_17'].sum() if self.biometric_df['bio_age_5_17'].sum() > 0 else 0
        demo_ratio = self.demographic_df['demo_age_17_'].sum() / self.demographic_df['demo_age_5_17'].sum() if self.demographic_df['demo_age_5_17'].sum() > 0 else 0
        
        print(f"  Biometric: 17+/5-17 ratio = {bio_ratio:.2f}")
        print(f"  Demographic: 17+/5-17 ratio = {demo_ratio:.2f}")
        
        # 3. Future demand estimation (children in 0-5 who will need biometric)
        print("\n3. Future Demand Estimation")
        print("-" * 80)
        children_0_5 = self.enrolment_df['age_0_5'].sum()
        print(f"  Children aged 0-5 enrolled: {children_0_5:,}")
        print(f"  These children will need biometric enrollment when they turn 5")
        print(f"  This represents potential future biometric demand")
        
        results['bio_age_totals'] = bio_age_totals
        results['demo_age_totals'] = demo_age_totals
        results['enrol_age_totals'] = enrol_age_totals
        results['children_0_5'] = children_0_5
        
        return results
    
    def calculate_derived_metrics(self):
        """Calculate derived intelligence metrics"""
        print(f"\n{'='*80}")
        print("DERIVED METRICS CALCULATION")
        print(f"{'='*80}")
        
        results = {}
        
        # Merge datasets on date, state, district, pincode
        print("\n1. Creating Integrated Dataset...")
        merged_df = self.biometric_df.merge(
            self.demographic_df,
            on=['date', 'state', 'district', 'pincode'],
            how='outer',
            suffixes=('_bio', '_demo')
        )
        merged_df = merged_df.merge(
            self.enrolment_df,
            on=['date', 'state', 'district', 'pincode'],
            how='outer'
        )
        merged_df = merged_df.fillna(0)
        
        # 1. Coverage Completeness Index
        print("\n2. Coverage Completeness Index")
        print("-" * 80)
        merged_df['demo_total'] = merged_df['demo_age_5_17'] + merged_df['demo_age_17_']
        merged_df['bio_total'] = merged_df['bio_age_5_17'] + merged_df['bio_age_17_']
        merged_df['coverage_index'] = np.where(
            merged_df['demo_total'] > 0,
            merged_df['bio_total'] / merged_df['demo_total'],
            np.nan
        )
        
        coverage_stats = merged_df['coverage_index'].describe()
        print(f"  Coverage Index Statistics:")
        print(f"    Mean: {coverage_stats['mean']:.3f}")
        print(f"    Median: {coverage_stats['50%']:.3f}")
        print(f"    Min: {coverage_stats['min']:.3f}")
        print(f"    Max: {coverage_stats['max']:.3f}")
        
        # Districts with low coverage (< 0.5)
        district_coverage = merged_df.groupby(['state', 'district']).agg({
            'coverage_index': 'mean',
            'demo_total': 'sum',
            'bio_total': 'sum'
        }).reset_index()
        low_coverage = district_coverage[
            (district_coverage['coverage_index'] < 0.5) & 
            (district_coverage['demo_total'] > 100)
        ].sort_values('coverage_index')
        
        print(f"\n  Districts with Low Coverage (< 0.5) and High Demographic Activity (>100):")
        print(f"    Found {len(low_coverage)} districts")
        if len(low_coverage) > 0:
            print(f"\n    Top 10 Districts Needing Attention:")
            for idx, row in low_coverage.head(10).iterrows():
                print(f"      {row['state']:20} - {row['district']:20}: "
                      f"Index={row['coverage_index']:.3f} "
                      f"(Demo: {row['demo_total']:,.0f}, Bio: {row['bio_total']:,.0f})")
        
        # 2. Update ratios
        print("\n3. Update Ratios Analysis")
        print("-" * 80)
        merged_df['bio_demo_ratio'] = np.where(
            merged_df['demo_total'] > 0,
            merged_df['bio_total'] / merged_df['demo_total'],
            np.nan
        )
        
        ratio_stats = merged_df['bio_demo_ratio'].describe()
        print(f"  Bio/Demo Ratio Statistics:")
        print(f"    Mean: {ratio_stats['mean']:.3f}")
        print(f"    Median: {ratio_stats['50%']:.3f}")
        
        results['merged_df'] = merged_df
        results['district_coverage'] = district_coverage
        results['low_coverage'] = low_coverage
        
        return results
    
    def detect_anomalies(self):
        """Detect anomalies and outliers"""
        print(f"\n{'='*80}")
        print("ANOMALY DETECTION")
        print(f"{'='*80}")
        
        results = {}
        
        # 1. Temporal anomalies (unusual spikes/drops)
        print("\n1. Temporal Anomalies (Daily Level)")
        print("-" * 80)
        
        daily_bio = self.biometric_df.groupby('date').agg({
            'bio_age_5_17': 'sum',
            'bio_age_17_': 'sum'
        }).reset_index()
        daily_bio['bio_total'] = daily_bio['bio_age_5_17'] + daily_bio['bio_age_17_']
        
        # Simple statistical outlier detection (Z-score > 3)
        mean_bio = daily_bio['bio_total'].mean()
        std_bio = daily_bio['bio_total'].std()
        daily_bio['z_score'] = (daily_bio['bio_total'] - mean_bio) / std_bio
        anomalies_bio = daily_bio[abs(daily_bio['z_score']) > 3].sort_values('bio_total', ascending=False)
        
        print(f"  Biometric anomalies (|Z-score| > 3): {len(anomalies_bio)} days")
        if len(anomalies_bio) > 0:
            print(f"\n  Top 10 Anomalous Days (Biometric):")
            for idx, row in anomalies_bio.head(10).iterrows():
                print(f"    {row['date'].date()}: {row['bio_total']:,.0f} updates (Z-score: {row['z_score']:.2f})")
        
        # 2. Geographic anomalies (unusual state/district activity)
        print("\n2. Geographic Anomalies")
        print("-" * 80)
        
        state_bio = self.biometric_df.groupby('state')['bio_age_5_17'].sum() + \
                   self.biometric_df.groupby('state')['bio_age_17_'].sum()
        state_mean = state_bio.mean()
        state_std = state_bio.std()
        state_z = (state_bio - state_mean) / state_std
        state_anomalies = state_z[abs(state_z) > 2].sort_values(ascending=False)
        
        print(f"  State-level anomalies (|Z-score| > 2): {len(state_anomalies)} states")
        if len(state_anomalies) > 0:
            print(f"\n  Anomalous States:")
            for state, z_score in state_anomalies.items():
                total = state_bio[state]
                print(f"    {state:25}: {total:10,.0f} updates (Z-score: {z_score:.2f})")
        
        results['anomalies_bio'] = anomalies_bio
        results['state_anomalies'] = state_anomalies
        
        return results
    
    def generate_insights(self, temporal_results, geo_results, age_results, metrics_results, anomaly_results):
        """Generate actionable insights from all analyses"""
        print(f"\n{'='*80}")
        print("KEY INSIGHTS SUMMARY")
        print(f"{'='*80}")
        
        insights = []
        
        # Insight 1: Coverage gaps
        if 'low_coverage' in metrics_results and len(metrics_results['low_coverage']) > 0:
            insight = {
                'category': 'Coverage Gap',
                'priority': 'High',
                'finding': f"{len(metrics_results['low_coverage'])} districts have low biometric coverage despite high demographic activity",
                'recommendation': 'Target these districts for biometric enrollment campaigns and resource allocation'
            }
            insights.append(insight)
            print(f"\n[INSIGHT 1] Coverage Gap (High Priority)")
            print(f"  Finding: {insight['finding']}")
            print(f"  Recommendation: {insight['recommendation']}")
        
        # Insight 2: Temporal patterns
        if 'daily_df' in temporal_results:
            daily_df = temporal_results['daily_df']
            trend_slope = np.polyfit(range(len(daily_df)), daily_df['bio_total'], 1)[0]
            if trend_slope > 100:
                insight = {
                    'category': 'Trend Analysis',
                    'priority': 'Medium',
                    'finding': 'Biometric updates showing strong increasing trend',
                    'recommendation': 'Prepare for increasing demand; scale resources accordingly'
                }
                insights.append(insight)
                print(f"\n[INSIGHT 2] Trend Analysis")
                print(f"  Finding: {insight['finding']}")
                print(f"  Recommendation: {insight['recommendation']}")
        
        # Insight 3: Geographic distribution
        if 'state_df' in geo_results:
            state_df = geo_results['state_df']
            top_state = state_df.iloc[0]
            insight = {
                'category': 'Geographic Distribution',
                'priority': 'Low',
                'finding': f"{top_state['state']} has the highest biometric update volume ({top_state['bio_total']:,.0f})",
                'recommendation': 'Monitor resource allocation in high-volume states'
            }
            insights.append(insight)
            print(f"\n[INSIGHT 3] Geographic Distribution")
            print(f"  Finding: {insight['finding']}")
            print(f"  Recommendation: {insight['recommendation']}")
        
        # Insight 4: Anomalies
        if 'anomalies_bio' in anomaly_results and len(anomaly_results['anomalies_bio']) > 0:
            anomaly_count = len(anomaly_results['anomalies_bio'])
            insight = {
                'category': 'Anomaly Detection',
                'priority': 'High',
                'finding': f"{anomaly_count} anomalous days detected in biometric updates",
                'recommendation': 'Investigate root causes of anomalies (events, system issues, data quality)'
            }
            insights.append(insight)
            print(f"\n[INSIGHT 4] Anomaly Detection")
            print(f"  Finding: {insight['finding']}")
            print(f"  Recommendation: {insight['recommendation']}")
        
        # Insight 5: Age transition
        if 'children_0_5' in age_results:
            children = age_results['children_0_5']
            insight = {
                'category': 'Future Demand',
                'priority': 'Medium',
                'finding': f"{children:,} children aged 0-5 will need biometric enrollment when they turn 5",
                'recommendation': 'Plan proactive enrollment campaigns for age transitions'
            }
            insights.append(insight)
            print(f"\n[INSIGHT 5] Future Demand")
            print(f"  Finding: {insight['finding']}")
            print(f"  Recommendation: {insight['recommendation']}")
        
        return insights
    
    def save_results(self, temporal_results, geo_results, age_results, metrics_results, anomaly_results, insights):
        """Save analysis results to files"""
        print(f"\n{'='*80}")
        print("SAVING RESULTS")
        print(f"{'='*80}")
        
        # Save daily aggregated data
        if 'daily_df' in temporal_results:
            output_path = self.results_path / 'daily_aggregated_data.csv'
            temporal_results['daily_df'].to_csv(output_path, index=False)
            print(f"  Saved: {output_path}")
        
        # Save state-level data
        if 'state_df' in geo_results:
            output_path = self.results_path / 'state_level_analysis.csv'
            geo_results['state_df'].to_csv(output_path, index=False)
            print(f"  Saved: {output_path}")
        
        # Save district coverage analysis
        if 'district_coverage' in metrics_results:
            output_path = self.results_path / 'district_coverage_analysis.csv'
            metrics_results['district_coverage'].to_csv(output_path, index=False)
            print(f"  Saved: {output_path}")
        
        # Save insights
        if insights:
            insights_df = pd.DataFrame(insights)
            output_path = self.results_path / 'key_insights.csv'
            insights_df.to_csv(output_path, index=False)
            print(f"  Saved: {output_path}")
        
        print(f"\n  All results saved to: {self.results_path}/")
    
    def run_full_analysis(self):
        """Execute complete exploratory data analysis"""
        print(f"\n{'='*80}")
        print("EXPLORATORY DATA ANALYSIS")
        print("AI-Driven Early Warning System for Aadhaar Update Surges")
        print(f"{'='*80}")
        
        # Run all analyses
        temporal_results = self.analyze_temporal_patterns()
        geo_results = self.analyze_geographic_patterns()
        age_results = self.analyze_age_patterns()
        metrics_results = self.calculate_derived_metrics()
        anomaly_results = self.detect_anomalies()
        
        # Generate insights
        insights = self.generate_insights(temporal_results, geo_results, age_results, metrics_results, anomaly_results)
        
        # Save results
        self.save_results(temporal_results, geo_results, age_results, metrics_results, anomaly_results, insights)
        
        print(f"\n{'='*80}")
        print("[SUCCESS] Exploratory Data Analysis Completed!")
        print(f"{'='*80}")
        print(f"\nNext Steps:")
        print("  1. Review analysis results in 'analysis_results/' directory")
        print("  2. Examine key insights for actionable recommendations")
        print("  3. Proceed with time-series forecasting models")
        print("  4. Implement advanced anomaly detection algorithms")
        print(f"{'='*80}")


def main():
    """Main execution function"""
    explorer = DataExplorer(data_path='processed_data')
    explorer.run_full_analysis()


if __name__ == "__main__":
    main()
