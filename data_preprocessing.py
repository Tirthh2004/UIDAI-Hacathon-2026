"""
Data Preprocessing Pipeline for UIDAI Hackathon Project
AI-Driven Early Warning System for Aadhaar Update Surges and Anomalies

This script performs comprehensive data cleaning, preprocessing, and transformation
for enrolment, demographic, and biometric datasets.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class DataPreprocessor:
    """Data preprocessing pipeline for Aadhaar datasets"""
    
    def __init__(self, base_path='.'):
        """
        Initialize the preprocessor
        
        Args:
            base_path: Base directory path for the project
        """
        self.base_path = Path(base_path)
        self.processed_data_path = self.base_path / 'processed_data'
        self.processed_data_path.mkdir(exist_ok=True)
        
        # Define dataset paths
        self.biometric_path = self.base_path / 'api_data_aadhar_biometric'
        self.demographic_path = self.base_path / 'api_data_aadhar_demographic' / 'api_data_aadhar_demographic'
        self.enrolment_path = self.base_path / 'api_data_aadhar_enrolment' / 'api_data_aadhar_enrolment'
        
        # Storage for cleaned data
        self.biometric_df = None
        self.demographic_df = None
        self.enrolment_df = None
        
    def load_and_combine_csv_files(self, directory_path, dataset_name):
        """
        Load and combine multiple CSV files from a directory
        
        Args:
            directory_path: Path to directory containing CSV files
            dataset_name: Name of the dataset (for logging)
            
        Returns:
            Combined pandas DataFrame
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Find all CSV files in the directory
        csv_files = sorted(directory_path.glob('*.csv'))
        
        if not csv_files:
            raise ValueError(f"No CSV files found in {directory_path}")
        
        print(f"\n{'='*60}")
        print(f"Loading {dataset_name} dataset...")
        print(f"Found {len(csv_files)} CSV file(s)")
        
        dataframes = []
        
        for idx, csv_file in enumerate(csv_files, 1):
            try:
                print(f"  Loading file {idx}/{len(csv_files)}: {csv_file.name}")
                df = pd.read_csv(csv_file, low_memory=False)
                dataframes.append(df)
                print(f"    Rows: {len(df):,}, Columns: {len(df.columns)}")
            except Exception as e:
                print(f"    ERROR loading {csv_file.name}: {str(e)}")
                continue
        
        if not dataframes:
            raise ValueError(f"Failed to load any CSV files from {directory_path}")
        
        # Combine all dataframes
        print(f"\n  Combining {len(dataframes)} file(s)...")
        combined_df = pd.concat(dataframes, ignore_index=True)
        print(f"  Combined dataset shape: {combined_df.shape[0]:,} rows × {combined_df.shape[1]} columns")
        
        return combined_df
    
    def clean_biometric_data(self, df):
        """
        Clean biometric dataset
        
        Args:
            df: Raw biometric DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        print(f"\n{'='*60}")
        print("Cleaning Biometric Data...")
        
        df = df.copy()
        initial_shape = df.shape
        print(f"  Initial shape: {initial_shape[0]:,} rows × {initial_shape[1]} columns")
        
        # Remove duplicates
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            print(f"  Removing {duplicates:,} duplicate rows...")
            df = df.drop_duplicates().reset_index(drop=True)
        
        # Standardize column names (trim whitespace)
        df.columns = df.columns.str.strip()
        
        # Convert date column to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                print(f"  WARNING: {invalid_dates:,} rows with invalid dates removed")
                df = df.dropna(subset=['date']).reset_index(drop=True)
        
        # Handle missing values in categorical columns
        categorical_cols = ['state', 'district']
        for col in categorical_cols:
            if col in df.columns:
                missing = df[col].isna().sum()
                if missing > 0:
                    print(f"  WARNING: {missing:,} missing values in {col} - removing rows")
                    df = df.dropna(subset=[col]).reset_index(drop=True)
        
        # Handle numeric columns (bio_age_5_17, bio_age_17_)
        numeric_cols = [col for col in df.columns if col.startswith('bio_age') or col == 'pincode']
        for col in numeric_cols:
            if col in df.columns:
                # Fill missing values with 0 (no updates on that day)
                missing = df[col].isna().sum()
                if missing > 0:
                    print(f"  Filling {missing:,} missing values in {col} with 0")
                    df[col] = df[col].fillna(0)
                
                # Convert to integer
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                
                # Ensure non-negative values
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    print(f"  WARNING: {negative_count:,} negative values in {col} - setting to 0")
                    df.loc[df[col] < 0, col] = 0
        
        # Standardize text columns (trim whitespace, title case)
        for col in ['state', 'district']:
            if col in df.columns:
                df[col] = df[col].str.strip().str.title()
        
        # Validate pincode (should be 6 digits)
        if 'pincode' in df.columns:
            invalid_pincodes = (~df['pincode'].astype(str).str.match(r'^\d{6}$')).sum()
            if invalid_pincodes > 0:
                print(f"  WARNING: {invalid_pincodes:,} invalid pincodes found")
        
        final_shape = df.shape
        print(f"  Final shape: {final_shape[0]:,} rows × {final_shape[1]} columns")
        print(f"  Rows removed: {initial_shape[0] - final_shape[0]:,}")
        
        return df
    
    def clean_demographic_data(self, df):
        """
        Clean demographic dataset
        
        Args:
            df: Raw demographic DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        print(f"\n{'='*60}")
        print("Cleaning Demographic Data...")
        
        df = df.copy()
        initial_shape = df.shape
        print(f"  Initial shape: {initial_shape[0]:,} rows × {initial_shape[1]} columns")
        
        # Remove duplicates
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            print(f"  Removing {duplicates:,} duplicate rows...")
            df = df.drop_duplicates().reset_index(drop=True)
        
        # Standardize column names
        df.columns = df.columns.str.strip()
        
        # Convert date column to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                print(f"  WARNING: {invalid_dates:,} rows with invalid dates removed")
                df = df.dropna(subset=['date']).reset_index(drop=True)
        
        # Handle missing values in categorical columns
        categorical_cols = ['state', 'district']
        for col in categorical_cols:
            if col in df.columns:
                missing = df[col].isna().sum()
                if missing > 0:
                    print(f"  WARNING: {missing:,} missing values in {col} - removing rows")
                    df = df.dropna(subset=[col]).reset_index(drop=True)
        
        # Handle numeric columns (demo_age_5_17, demo_age_17_)
        numeric_cols = [col for col in df.columns if col.startswith('demo_age') or col == 'pincode']
        for col in numeric_cols:
            if col in df.columns:
                missing = df[col].isna().sum()
                if missing > 0:
                    print(f"  Filling {missing:,} missing values in {col} with 0")
                    df[col] = df[col].fillna(0)
                
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    print(f"  WARNING: {negative_count:,} negative values in {col} - setting to 0")
                    df.loc[df[col] < 0, col] = 0
        
        # Standardize text columns
        for col in ['state', 'district']:
            if col in df.columns:
                df[col] = df[col].str.strip().str.title()
        
        # Validate pincode
        if 'pincode' in df.columns:
            invalid_pincodes = (~df['pincode'].astype(str).str.match(r'^\d{6}$')).sum()
            if invalid_pincodes > 0:
                print(f"  WARNING: {invalid_pincodes:,} invalid pincodes found")
        
        final_shape = df.shape
        print(f"  Final shape: {final_shape[0]:,} rows × {final_shape[1]} columns")
        print(f"  Rows removed: {initial_shape[0] - final_shape[0]:,}")
        
        return df
    
    def clean_enrolment_data(self, df):
        """
        Clean enrolment dataset
        
        Args:
            df: Raw enrolment DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        print(f"\n{'='*60}")
        print("Cleaning Enrolment Data...")
        
        df = df.copy()
        initial_shape = df.shape
        print(f"  Initial shape: {initial_shape[0]:,} rows × {initial_shape[1]} columns")
        
        # Remove duplicates
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            print(f"  Removing {duplicates:,} duplicate rows...")
            df = df.drop_duplicates().reset_index(drop=True)
        
        # Standardize column names
        df.columns = df.columns.str.strip()
        
        # Convert date column to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                print(f"  WARNING: {invalid_dates:,} rows with invalid dates removed")
                df = df.dropna(subset=['date']).reset_index(drop=True)
        
        # Handle missing values in categorical columns
        categorical_cols = ['state', 'district']
        for col in categorical_cols:
            if col in df.columns:
                missing = df[col].isna().sum()
                if missing > 0:
                    print(f"  WARNING: {missing:,} missing values in {col} - removing rows")
                    df = df.dropna(subset=[col]).reset_index(drop=True)
        
        # Handle numeric columns (age_0_5, age_5_17, age_18_greater)
        numeric_cols = [col for col in df.columns if col.startswith('age_') or col == 'pincode']
        for col in numeric_cols:
            if col in df.columns:
                missing = df[col].isna().sum()
                if missing > 0:
                    print(f"  Filling {missing:,} missing values in {col} with 0")
                    df[col] = df[col].fillna(0)
                
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    print(f"  WARNING: {negative_count:,} negative values in {col} - setting to 0")
                    df.loc[df[col] < 0, col] = 0
        
        # Standardize text columns
        for col in ['state', 'district']:
            if col in df.columns:
                df[col] = df[col].str.strip().str.title()
        
        # Validate pincode
        if 'pincode' in df.columns:
            invalid_pincodes = (~df['pincode'].astype(str).str.match(r'^\d{6}$')).sum()
            if invalid_pincodes > 0:
                print(f"  WARNING: {invalid_pincodes:,} invalid pincodes found")
        
        final_shape = df.shape
        print(f"  Final shape: {final_shape[0]:,} rows × {final_shape[1]} columns")
        print(f"  Rows removed: {initial_shape[0] - final_shape[0]:,}")
        
        return df
    
    def generate_data_summary(self, df, dataset_name):
        """
        Generate summary statistics for a dataset
        
        Args:
            df: DataFrame to summarize
            dataset_name: Name of the dataset
        """
        print(f"\n{'='*60}")
        print(f"Data Summary: {dataset_name}")
        print(f"{'='*60}")
        print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
        print(f"\nDate Range:")
        if 'date' in df.columns:
            print(f"  From: {df['date'].min()}")
            print(f"  To: {df['date'].max()}")
            print(f"  Total days: {(df['date'].max() - df['date'].min()).days + 1}")
        
        print(f"\nGeographic Coverage:")
        if 'state' in df.columns:
            print(f"  States: {df['state'].nunique()}")
        if 'district' in df.columns:
            print(f"  Districts: {df['district'].nunique()}")
        if 'pincode' in df.columns:
            print(f"  Pincodes: {df['pincode'].nunique()}")
        
        print(f"\nNumeric Columns Summary:")
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            summary = df[numeric_cols].describe()
            print(summary.to_string())
        
        print(f"\nData Quality Checks:")
        print(f"  Missing values: {df.isnull().sum().sum()}")
        print(f"  Duplicate rows: {df.duplicated().sum()}")
        
        if 'date' in df.columns:
            future_dates = (df['date'] > pd.Timestamp.now()).sum()
            if future_dates > 0:
                print(f"  WARNING: {future_dates:,} rows with future dates")
    
    def process_all_datasets(self):
        """Process all three datasets"""
        print(f"\n{'='*80}")
        print("UIDAI Data Preprocessing Pipeline")
        print("AI-Driven Early Warning System for Aadhaar Update Surges")
        print(f"{'='*80}")
        
        try:
            # Load and combine Biometric data
            print("\n[1/3] Processing Biometric Data...")
            raw_biometric = self.load_and_combine_csv_files(self.biometric_path, "Biometric")
            self.biometric_df = self.clean_biometric_data(raw_biometric)
            self.generate_data_summary(self.biometric_df, "Biometric Data")
            
            # Load and combine Demographic data
            print("\n[2/3] Processing Demographic Data...")
            raw_demographic = self.load_and_combine_csv_files(self.demographic_path, "Demographic")
            self.demographic_df = self.clean_demographic_data(raw_demographic)
            self.generate_data_summary(self.demographic_df, "Demographic Data")
            
            # Load and combine Enrolment data
            print("\n[3/3] Processing Enrolment Data...")
            raw_enrolment = self.load_and_combine_csv_files(self.enrolment_path, "Enrolment")
            self.enrolment_df = self.clean_enrolment_data(raw_enrolment)
            self.generate_data_summary(self.enrolment_df, "Enrolment Data")
            
            # Save cleaned data
            print(f"\n{'='*60}")
            print("Saving Cleaned Data...")
            self.save_cleaned_data()
            
            print(f"\n{'='*80}")
            print("[SUCCESS] Data Preprocessing Completed Successfully!")
            print(f"{'='*80}")
            
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"ERROR: Data preprocessing failed!")
            print(f"Error: {str(e)}")
            print(f"{'='*60}")
            raise
    
    def save_cleaned_data(self):
        """Save cleaned datasets to processed_data directory"""
        if self.biometric_df is not None:
            output_path = self.processed_data_path / 'biometric_cleaned.csv'
            print(f"  Saving biometric data to {output_path}...")
            self.biometric_df.to_csv(output_path, index=False)
            print(f"    Saved {len(self.biometric_df):,} rows")
        
        if self.demographic_df is not None:
            output_path = self.processed_data_path / 'demographic_cleaned.csv'
            print(f"  Saving demographic data to {output_path}...")
            self.demographic_df.to_csv(output_path, index=False)
            print(f"    Saved {len(self.demographic_df):,} rows")
        
        if self.enrolment_df is not None:
            output_path = self.processed_data_path / 'enrolment_cleaned.csv'
            print(f"  Saving enrolment data to {output_path}...")
            self.enrolment_df.to_csv(output_path, index=False)
            print(f"    Saved {len(self.enrolment_df):,} rows")


def main():
    """Main execution function"""
    # Initialize preprocessor
    preprocessor = DataPreprocessor(base_path='.')
    
    # Process all datasets
    preprocessor.process_all_datasets()
    
    print("\n" + "="*80)
    print("Next Steps:")
    print("="*80)
    print("1. Review the cleaned data in 'processed_data/' directory")
    print("2. Check data summaries above for any warnings")
    print("3. Proceed with exploratory data analysis and feature engineering")
    print("4. Build forecasting and anomaly detection models")
    print("="*80)


if __name__ == "__main__":
    main()
