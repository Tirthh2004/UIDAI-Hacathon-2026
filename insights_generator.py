"""
Actionable Insights Generation Module
AI-Driven Early Warning System for Aadhaar Update Surges

This module translates predictions, anomalies, and forecasts into actionable insights:
- Resource deployment recommendations
- Targeted campaign suggestions
- Operational investigation prompts
- Capacity planning insights
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import json
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')


class InsightsGenerator:
    """
    Generate actionable insights from predictions and anomalies
    
    Capability: Insight Generation
    Input Sources: Surge predictions, Anomalies, Forecasts, Patterns
    Output: Structured recommendations with priorities and action items
    """
    
    def __init__(self, output_path='insights_results'):
        """
        Initialize the Insights Generator
        
        Args:
            output_path: Path to save insights results
        """
        self.output_path = Path(output_path)
        self.output_path.mkdir(exist_ok=True)
        
        # Data sources
        self.surge_predictions = None
        self.anomalies = None
        self.forecasts = None
        self.patterns = None
        self.district_results = None
        
        # Storage for insights
        self.insights = []
        
    def load_data(self):
        """Load all prediction and analysis results"""
        print("Loading data sources...")
        
        loaded_sources = []
        
        # Load surge predictions
        surge_path = Path('surge_results')
        if (surge_path / 'surge_predictions.csv').exists():
            try:
                self.surge_predictions = pd.read_csv(
                    surge_path / 'surge_predictions.csv',
                    parse_dates=['predicted_date']
                )
                loaded_sources.append(f"Surge predictions ({len(self.surge_predictions)} predictions)")
            except Exception as e:
                print(f"  Warning: Could not load surge predictions: {e}")
        
        # Load anomaly detection results
        anomaly_path = Path('anomaly_results')
        if (anomaly_path / 'anomalies_detected.csv').exists():
            try:
                self.anomalies = pd.read_csv(anomaly_path / 'anomalies_detected.csv')
                if 'date' in self.anomalies.columns:
                    self.anomalies['date'] = pd.to_datetime(self.anomalies['date'], errors='coerce')
                loaded_sources.append(f"Anomalies ({len(self.anomalies)} anomalies)")
            except Exception as e:
                print(f"  Warning: Could not load anomalies: {e}")
        
        # Load forecasting results
        forecast_path = Path('forecast_results')
        if (forecast_path / 'state_forecasts.csv').exists():
            try:
                self.forecasts = pd.read_csv(forecast_path / 'state_forecasts.csv')
                loaded_sources.append(f"Forecasts ({len(self.forecasts)} forecast records)")
            except Exception as e:
                print(f"  Warning: Could not load forecasts: {e}")
        
        # Load pattern learning results
        pattern_path = Path('pattern_results')
        if (pattern_path / 'state_patterns_summary.csv').exists():
            try:
                self.patterns = pd.read_csv(pattern_path / 'state_patterns_summary.csv')
                loaded_sources.append(f"Patterns ({len(self.patterns)} state patterns)")
            except Exception as e:
                print(f"  Warning: Could not load patterns: {e}")
        
        # Load district/pincode results
        district_path = Path('district_pincode_results')
        if (district_path / 'district_forecasts.csv').exists():
            try:
                self.district_results = pd.read_csv(district_path / 'district_forecasts.csv')
                loaded_sources.append(f"District results ({len(self.district_results)} district forecasts)")
            except Exception as e:
                print(f"  Warning: Could not load district results: {e}")
        
        print(f"  Loaded {len(loaded_sources)} data sources:")
        for source in loaded_sources:
            print(f"    - {source}")
        
        return len(loaded_sources) > 0
    
    def generate_resource_deployment_insights(self):
        """
        Generate resource deployment recommendations based on surge predictions
        
        Returns:
            List of resource deployment insights
        """
        insights = []
        
        if self.surge_predictions is None or len(self.surge_predictions) == 0:
            return insights
        
        print("\nGenerating resource deployment insights...")
        
        # Get high-priority surges (High priority, within 60 days)
        high_priority_surges = self.surge_predictions[
            (self.surge_predictions['priority'] == 'High') &
            (self.surge_predictions['days_until_surge'] <= 60)
        ].copy()
        
        # Group by state
        for state in high_priority_surges['state'].dropna().unique():
            state_surges = high_priority_surges[high_priority_surges['state'] == state]
            
            # Calculate total expected volume
            total_volume = state_surges['estimated_volume'].sum()
            avg_magnitude = state_surges['expected_magnitude'].mean()
            min_days_until = state_surges['days_until_surge'].min()
            max_days_until = state_surges['days_until_surge'].max()
            
            # Determine priority based on volume and urgency
            if total_volume > 5000000 and min_days_until <= 30:
                priority = 'Critical'
                impact = 'High'
            elif total_volume > 3000000 or min_days_until <= 45:
                priority = 'High'
                impact = 'High'
            else:
                priority = 'Medium'
                impact = 'Medium'
            
            # Estimate resource requirements (example: 1 enrollment center per 100K volume)
            estimated_centers = max(1, int(total_volume / 100000))
            estimated_staff = estimated_centers * 5  # 5 staff per center
            
            insight = {
                'insight_type': 'resource_deployment',
                'title': f'Deploy Additional Resources to {state}',
                'priority': priority,
                'impact': impact,
                'state': state,
                'district': None,
                'rationale': f'High-priority surge predicted with {len(state_surges)} surge event(s). Expected volume: {total_volume:,.0f}, Magnitude: {avg_magnitude:.2f}x normal',
                'expected_impact': f'Prepare for {total_volume:,.0f} expected updates within {min_days_until}-{max_days_until} days',
                'action_items': [
                    f'Deploy {estimated_centers} additional enrollment centers to {state}',
                    f'Allocate {estimated_staff} additional staff members',
                    f'Begin resource allocation within {max(1, min_days_until - 14)} days',
                    'Coordinate with state authorities for center locations',
                    'Set up temporary enrollment centers if needed'
                ],
                'timeline': f'{min_days_until}-{max_days_until} days',
                'estimated_volume': total_volume,
                'confidence': state_surges['confidence'].mean()
            }
            insights.append(insight)
        
        print(f"  Generated {len(insights)} resource deployment insights")
        return insights
    
    def generate_campaign_insights(self):
        """
        Generate targeted campaign suggestions based on patterns and anomalies
        
        Returns:
            List of campaign insights
        """
        insights = []
        
        print("\nGenerating campaign insights...")
        
        # Campaign insights from anomalies
        if self.anomalies is not None and len(self.anomalies) > 0:
            # Geographic anomalies - areas with low enrollment relative to demographics
            geo_anomalies = self.anomalies[
                (self.anomalies['detection_level'] == 'geographic') &
                (self.anomalies['severity'] >= 0.7)
            ].copy()
            
            if len(geo_anomalies) > 0:
                # Group by state
                for state in geo_anomalies['state'].dropna().unique():
                    state_anomalies = geo_anomalies[geo_anomalies['state'] == state]
                    
                    # Identify if it's a coverage gap (low enrollment)
                    low_enrollment = state_anomalies[
                        (state_anomalies['metric'].str.contains('bio_total|demo_total', na=False)) &
                        (state_anomalies['value'] < state_anomalies['lower_bound'])
                    ]
                    
                    if len(low_enrollment) > 0:
                        priority = 'High' if len(low_enrollment) >= 5 else 'Medium'
                        impact = 'High'
                        
                        insight = {
                            'insight_type': 'targeted_campaign',
                            'title': f'Awareness Campaign Needed in {state}',
                            'priority': priority,
                            'impact': impact,
                            'state': state,
                            'district': None,
                            'rationale': f'Detected {len(low_enrollment)} geographic anomalies indicating low enrollment rates relative to demographics in {state}',
                            'expected_impact': 'Increase enrollment rates and close coverage gaps',
                            'action_items': [
                                f'Launch awareness campaign in {state}',
                                'Focus on biometric enrollment importance',
                                'Collaborate with local government and NGOs',
                                'Set up enrollment drives in low-coverage areas',
                                'Use mobile enrollment units for remote areas',
                                'Monitor campaign effectiveness through enrollment metrics'
                            ],
                            'timeline': 'Immediate (1-2 weeks)',
                            'campaign_type': 'Awareness & Enrollment Drive'
                        }
                        insights.append(insight)
        
        # Campaign insights from surge predictions (pre-surge campaigns)
        if self.surge_predictions is not None and len(self.surge_predictions) > 0:
            upcoming_surges = self.surge_predictions[
                (self.surge_predictions['days_until_surge'] > 30) &
                (self.surge_predictions['days_until_surge'] <= 90)
            ].copy()
            
            for state in upcoming_surges['state'].dropna().unique():
                state_surges = upcoming_surges[upcoming_surges['state'] == state]
                
                if len(state_surges) > 0:
                    insight = {
                        'insight_type': 'targeted_campaign',
                        'title': f'Pre-Surge Preparation Campaign in {state}',
                        'priority': 'Medium',
                        'impact': 'Medium',
                        'state': state,
                        'district': None,
                        'rationale': f'Surge predicted in {state} within 30-90 days. Pre-campaign can help prepare population and reduce surge impact',
                        'expected_impact': 'Prepare population for upcoming surge, potentially flattening the surge curve',
                        'action_items': [
                            f'Begin awareness campaign in {state} before surge hits',
                            'Encourage early enrollment to reduce surge volume',
                            'Set up pre-enrollment registration system',
                            'Provide information about required documents',
                            'Coordinate with local enrollment centers'
                        ],
                        'timeline': f'Within next {(state_surges["days_until_surge"].min() - 14):.0f} days',
                        'campaign_type': 'Pre-Surge Preparation'
                    }
                    insights.append(insight)
        
        print(f"  Generated {len(insights)} campaign insights")
        return insights
    
    def generate_investigation_insights(self):
        """
        Generate operational investigation prompts based on anomalies
        
        Returns:
            List of investigation insights
        """
        insights = []
        
        print("\nGenerating investigation insights...")
        
        if self.anomalies is None or len(self.anomalies) == 0:
            return insights
        
        # High-severity anomalies requiring investigation
        high_severity = self.anomalies[
            (self.anomalies['severity'] >= 0.8) |
            (self.anomalies['mad_z_score'].abs() > 5)
        ].copy()
        
        if len(high_severity) == 0:
            return insights
        
        # Temporal anomalies (unusual patterns in time)
        temporal_anomalies = high_severity[high_severity['detection_level'] == 'temporal'].copy()
        if len(temporal_anomalies) > 0:
            # Group recent anomalies (within last 30 days if date available)
            if 'date' in temporal_anomalies.columns:
                latest_date = pd.to_datetime(temporal_anomalies['date']).max()
                recent_anomalies = temporal_anomalies[
                    pd.to_datetime(temporal_anomalies['date']) >= (latest_date - timedelta(days=30))
                ]
            else:
                recent_anomalies = temporal_anomalies.head(10)
            
            if len(recent_anomalies) > 0:
                # Identify unusual drops (zero or near-zero values)
                zero_values = recent_anomalies[recent_anomalies['value'] == 0]
                if len(zero_values) > 0:
                    insight = {
                        'insight_type': 'operational_investigation',
                        'title': 'Investigate Zero Enrollment Days',
                        'priority': 'Critical',
                        'impact': 'High',
                        'state': None,
                        'district': None,
                        'rationale': f'Detected {len(zero_values)} days with zero enrollment values. This may indicate system issues, data collection problems, or operational disruptions',
                        'expected_impact': 'Identify and resolve root cause of zero enrollment days',
                        'action_items': [
                            'Review system logs for the identified dates',
                            'Check for data collection system failures',
                            'Investigate operational disruptions (holidays, strikes, etc.)',
                            'Verify data pipeline integrity',
                            'Check for system maintenance windows',
                            'Review enrollment center operations'
                        ],
                        'timeline': 'Immediate (within 24-48 hours)',
                        'anomaly_count': len(zero_values),
                        'anomaly_type': 'Zero enrollment values'
                    }
                    insights.append(insight)
        
        # Ratio anomalies (unusual biometric/demographic ratios)
        ratio_anomalies = high_severity[
            high_severity['detection_level'] == 'ratio'
        ].copy()
        
        if len(ratio_anomalies) > 0:
            insight = {
                'insight_type': 'operational_investigation',
                'title': 'Investigate Unusual Biometric/Demographic Ratios',
                'priority': 'High',
                'impact': 'Medium',
                'state': None,
                'district': None,
                'rationale': f'Detected {len(ratio_anomalies)} anomalies in biometric/demographic ratios. Unusual ratios may indicate process issues, data quality problems, or coverage gaps',
                'expected_impact': 'Identify process improvements and data quality issues',
                'action_items': [
                    'Review enrollment process in affected areas',
                    'Investigate data collection and recording procedures',
                    'Check for systematic biases in enrollment',
                    'Analyze demographic vs biometric enrollment patterns',
                    'Review training needs for enrollment centers'
                ],
                'timeline': 'Within 1 week',
                'anomaly_count': len(ratio_anomalies),
                'anomaly_type': 'Ratio anomalies'
            }
            insights.append(insight)
        
        # Geographic anomalies (states/districts with unusual patterns)
        geo_anomalies = high_severity[
            (high_severity['detection_level'] == 'geographic') &
            (high_severity['state'].notna())
        ].copy()
        
        if len(geo_anomalies) > 0:
            # Group by state
            state_counts = geo_anomalies['state'].value_counts()
            top_anomaly_states = state_counts.head(5)
            
            for state, count in top_anomaly_states.items():
                if count >= 5:  # States with 5+ high-severity anomalies
                    insight = {
                        'insight_type': 'operational_investigation',
                        'title': f'Investigate Patterns in {state}',
                        'priority': 'High',
                        'impact': 'Medium',
                        'state': state,
                        'district': None,
                        'rationale': f'Detected {count} high-severity geographic anomalies in {state}. This indicates consistent unusual patterns requiring investigation',
                        'expected_impact': 'Identify systemic issues or operational patterns in the state',
                        'action_items': [
                            f'Conduct operational review in {state}',
                            'Compare enrollment patterns with similar states',
                            'Review state-specific policies and procedures',
                            'Interview state enrollment center managers',
                            'Analyze state-level data quality',
                            'Check for regional process variations'
                        ],
                        'timeline': 'Within 2 weeks',
                        'anomaly_count': count,
                        'anomaly_type': 'Geographic pattern anomalies'
                    }
                    insights.append(insight)
        
        print(f"  Generated {len(insights)} investigation insights")
        return insights
    
    def generate_capacity_planning_insights(self):
        """
        Generate capacity planning insights based on forecasts and patterns
        
        Returns:
            List of capacity planning insights
        """
        insights = []
        
        print("\nGenerating capacity planning insights...")
        
        # Capacity planning from forecasts
        if self.forecasts is not None and len(self.forecasts) > 0:
            # Get short-term forecasts (next 1-3 months)
            short_term = self.forecasts[self.forecasts['forecast_type'] == 'short_term'].copy()
            
            if len(short_term) > 0:
                # Calculate average forecast by state
                state_forecasts = short_term.groupby('state').agg({
                    'forecast_value': 'mean',
                    'conf_upper': 'mean'
                }).reset_index()
                state_forecasts = state_forecasts.sort_values('forecast_value', ascending=False)
                
                # Identify states with highest forecasted volumes
                top_states = state_forecasts.head(10)
                
                for idx, row in top_states.iterrows():
                    state = row['state']
                    avg_forecast = row['forecast_value']
                    conf_upper = row['conf_upper']
                    
                    # Estimate capacity requirements
                    estimated_centers = max(1, int(avg_forecast / 50000))  # 1 center per 50K forecast
                    
                    priority = 'High' if avg_forecast > 100000 else 'Medium'
                    impact = 'High' if avg_forecast > 200000 else 'Medium'
                    
                    insight = {
                        'insight_type': 'capacity_planning',
                        'title': f'Capacity Planning for {state}',
                        'priority': priority,
                        'impact': impact,
                        'state': state,
                        'district': None,
                        'rationale': f'Short-term forecasts indicate average daily volume of {avg_forecast:,.0f} (upper bound: {conf_upper:,.0f}) for {state}. Current capacity may be insufficient',
                        'expected_impact': 'Ensure adequate capacity to handle forecasted demand',
                        'action_items': [
                            f'Review current capacity in {state}',
                            f'Plan for {estimated_centers} enrollment centers',
                            'Assess current center utilization rates',
                            'Identify capacity expansion needs',
                            'Plan staffing requirements',
                            'Coordinate infrastructure upgrades if needed',
                            'Consider temporary capacity increases'
                        ],
                        'timeline': 'Within 1-2 months',
                        'forecasted_volume': avg_forecast,
                        'forecast_period': 'Short-term (1-3 months)'
                    }
                    insights.append(insight)
        
        # Capacity planning from patterns (trends)
        if self.patterns is not None and len(self.patterns) > 0:
            # Identify states with increasing trends
            if 'trend_direction' in self.patterns.columns:
                increasing_trends = self.patterns[
                    (self.patterns['trend_direction'] == 'increasing') &
                    (self.patterns['trend_slope'] > 0.1)  # Significant positive slope
                ].copy()
                
                if len(increasing_trends) > 0:
                    # Group by state if state column exists
                    if 'state' in increasing_trends.columns:
                        for state in increasing_trends['state'].unique():
                            state_patterns = increasing_trends[increasing_trends['state'] == state]
                            avg_slope = state_patterns['trend_slope'].mean()
                            
                            insight = {
                                'insight_type': 'capacity_planning',
                                'title': f'Long-term Capacity Planning for {state}',
                                'priority': 'Medium',
                                'impact': 'Medium',
                                'state': state,
                                'district': None,
                                'rationale': f'{state} shows consistent increasing trend (slope: {avg_slope:.3f}). Long-term capacity planning needed to accommodate growth',
                                'expected_impact': 'Prepare for sustained growth in enrollment demand',
                                'action_items': [
                                    f'Develop long-term capacity plan for {state}',
                                    'Assess infrastructure needs for next 6-12 months',
                                    'Plan for permanent capacity expansion',
                                    'Coordinate with state authorities for infrastructure',
                                    'Consider technology upgrades to increase efficiency',
                                    'Monitor trend continuation'
                                ],
                                'timeline': '3-6 months',
                                'trend_slope': avg_slope,
                                'planning_period': 'Long-term (6-12 months)'
                            }
                            insights.append(insight)
        
        # Capacity planning from district-level forecasts
        if self.district_results is not None and len(self.district_results) > 0:
            if 'district' in self.district_results.columns and 'forecast_value' in self.district_results.columns:
                # Identify districts with high forecasted volumes
                district_forecasts = self.district_results.groupby('district').agg({
                    'forecast_value': 'mean'
                }).reset_index()
                district_forecasts = district_forecasts.sort_values('forecast_value', ascending=False)
                
                top_districts = district_forecasts.head(10)
                
                for idx, row in top_districts.iterrows():
                    district = row['district']
                    avg_forecast = row['forecast_value']
                    
                    if avg_forecast > 50000:  # Only highlight significant forecasts
                        insight = {
                            'insight_type': 'capacity_planning',
                            'title': f'District-level Capacity Planning: {district}',
                            'priority': 'Medium',
                            'impact': 'Medium',
                            'state': None,
                            'district': district,
                            'rationale': f'District {district} shows high forecasted volumes ({avg_forecast:,.0f}). District-level capacity planning recommended',
                            'expected_impact': 'Ensure adequate district-level capacity',
                            'action_items': [
                                f'Review enrollment centers in {district}',
                                'Assess district-level capacity requirements',
                                'Coordinate with district administration',
                                'Plan for local capacity expansion',
                                'Consider mobile enrollment units'
                            ],
                            'timeline': 'Within 2-3 months',
                            'forecasted_volume': avg_forecast,
                            'planning_level': 'District'
                        }
                        insights.append(insight)
        
        print(f"  Generated {len(insights)} capacity planning insights")
        return insights
    
    def generate_all_insights(self):
        """
        Generate all types of insights
        
        Returns:
            DataFrame with all insights
        """
        print(f"\n{'='*80}")
        print("ACTIONABLE INSIGHTS GENERATION")
        print(f"{'='*80}")
        
        self.insights = []
        
        # Generate all insight types
        self.insights.extend(self.generate_resource_deployment_insights())
        self.insights.extend(self.generate_campaign_insights())
        self.insights.extend(self.generate_investigation_insights())
        self.insights.extend(self.generate_capacity_planning_insights())
        
        # Convert to DataFrame
        if len(self.insights) > 0:
            insights_df = pd.DataFrame(self.insights)
            
            # Add insight ID
            insights_df['insight_id'] = range(1, len(insights_df) + 1)
            
            # Reorder columns
            col_order = ['insight_id', 'insight_type', 'title', 'priority', 'impact', 'state', 'district',
                        'rationale', 'expected_impact', 'action_items', 'timeline']
            other_cols = [c for c in insights_df.columns if c not in col_order]
            insights_df = insights_df[col_order + other_cols]
            
            # Sort by priority (Critical > High > Medium > Low)
            priority_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
            insights_df['priority_order'] = insights_df['priority'].map(priority_order)
            insights_df = insights_df.sort_values(['priority_order', 'impact'], ascending=[True, False])
            insights_df = insights_df.drop('priority_order', axis=1)
            
            print(f"\nTotal insights generated: {len(insights_df)}")
            print(f"  Resource Deployment: {len(insights_df[insights_df['insight_type'] == 'resource_deployment'])}")
            print(f"  Targeted Campaigns: {len(insights_df[insights_df['insight_type'] == 'targeted_campaign'])}")
            print(f"  Operational Investigations: {len(insights_df[insights_df['insight_type'] == 'operational_investigation'])}")
            print(f"  Capacity Planning: {len(insights_df[insights_df['insight_type'] == 'capacity_planning'])}")
            
            print(f"\nBy Priority:")
            for priority in ['Critical', 'High', 'Medium', 'Low']:
                count = len(insights_df[insights_df['priority'] == priority])
                if count > 0:
                    print(f"  {priority}: {count}")
            
            return insights_df
        else:
            print("\n[WARNING] No insights generated. Check data sources.")
            return pd.DataFrame()
    
    def save_results(self, insights_df):
        """
        Save insights to files
        
        Args:
            insights_df: DataFrame with insights
        """
        print(f"\n{'='*80}")
        print("SAVING RESULTS")
        print(f"{'='*80}")
        
        if len(insights_df) == 0:
            print("\n[WARNING] No insights to save.")
            return
        
        # Convert action_items list to string for CSV
        insights_csv = insights_df.copy()
        if 'action_items' in insights_csv.columns:
            insights_csv['action_items'] = insights_csv['action_items'].apply(
                lambda x: '; '.join(x) if isinstance(x, list) else str(x)
            )
        
        # Save all insights
        output_file = self.output_path / 'actionable_insights.csv'
        insights_csv.to_csv(output_file, index=False)
        print(f"\n[SUCCESS] Saved: {output_file}")
        print(f"   Total insights: {len(insights_df)}")
        
        # Save by insight type
        for insight_type in insights_df['insight_type'].unique():
            type_df = insights_df[insights_df['insight_type'] == insight_type]
            type_file = self.output_path / f'insights_{insight_type}.csv'
            type_csv = type_df.copy()
            if 'action_items' in type_csv.columns:
                type_csv['action_items'] = type_csv['action_items'].apply(
                    lambda x: '; '.join(x) if isinstance(x, list) else str(x)
                )
            type_csv.to_csv(type_file, index=False)
            print(f"[SUCCESS] Saved: {type_file} ({len(type_df)} insights)")
        
        # Save by priority
        for priority in insights_df['priority'].unique():
            priority_df = insights_df[insights_df['priority'] == priority]
            priority_file = self.output_path / f'insights_priority_{priority.lower()}.csv'
            priority_csv = priority_df.copy()
            if 'action_items' in priority_csv.columns:
                priority_csv['action_items'] = priority_csv['action_items'].apply(
                    lambda x: '; '.join(x) if isinstance(x, list) else str(x)
                )
            priority_csv.to_csv(priority_file, index=False)
            print(f"[SUCCESS] Saved: {priority_file} ({len(priority_df)} insights)")
        
        # Create summary JSON
        summary = {
            'total_insights': len(insights_df),
            'generation_date': datetime.now().isoformat(),
            'by_insight_type': {},
            'by_priority': {},
            'by_impact': {},
            'top_insights': []
        }
        
        for insight_type in insights_df['insight_type'].unique():
            summary['by_insight_type'][insight_type] = len(insights_df[insights_df['insight_type'] == insight_type])
        
        for priority in insights_df['priority'].unique():
            summary['by_priority'][priority] = len(insights_df[insights_df['priority'] == priority])
        
        for impact in insights_df['impact'].unique():
            summary['by_impact'][impact] = len(insights_df[insights_df['impact'] == impact])
        
        # Top 10 insights (by priority and impact)
        top_insights = insights_df.head(10)[['insight_id', 'insight_type', 'title', 'priority', 'impact', 'state']].to_dict('records')
        summary['top_insights'] = top_insights
        
        # Save summary JSON
        summary_file = self.output_path / 'insights_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"[SUCCESS] Saved: {summary_file}")
        
        # Save detailed JSON (with action items as lists)
        detailed_json_file = self.output_path / 'actionable_insights.json'
        insights_dict = insights_df.to_dict('records')
        with open(detailed_json_file, 'w') as f:
            json.dump(insights_dict, f, indent=2, default=str)
        print(f"[SUCCESS] Saved: {detailed_json_file}")
    
    def run(self):
        """Run the complete insights generation pipeline"""
        if not self.load_data():
            print("\n[ERROR] Could not load data sources. Please ensure prediction and analysis modules have been run.")
            return False
        
        insights_df = self.generate_all_insights()
        self.save_results(insights_df)
        
        print(f"\n{'='*80}")
        print("[SUCCESS] Actionable Insights Generation Completed!")
        print(f"{'='*80}")
        
        return True


if __name__ == "__main__":
    generator = InsightsGenerator()
    generator.run()
