#!/usr/bin/env python3
"""
CSV Separator - Transform political compass results from long to wide format
Converts the detailed survey results into a compact format with one row per question
and columns for each religion's prediction.
"""

import pandas as pd
import argparse
import sys
from pathlib import Path
from typing import Optional

def transform_csv(input_file: str, output_file: Optional[str] = None):
    """
    Transform CSV from long format to wide format
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path for output CSV (optional, auto-generated if not provided)
    """
    
    try:
        # Read the input CSV
        print(f"📖 Reading input file: {input_file}")
        df = pd.read_csv(input_file)
        
        # Check if required columns exist
        required_cols = ['question_id', 'statement', 'religion', 'choice']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        print(f"✅ Loaded {len(df)} rows with {len(df.columns)} columns")
        print(f"📊 Found {df['question_id'].nunique()} unique questions")
        print(f"🌍 Found {df['religion'].nunique()} unique religions/beliefs")
        
        # Get unique religions in order
        religions = sorted(df['religion'].unique())
        print(f"🔍 Religions found: {', '.join(religions)}")
        
        # Create the wide format
        print("🔄 Transforming to wide format...")
        
        # Start with question info with proper numerical sorting
        question_info = df[['question_id', 'statement']].drop_duplicates()
        # Sort by numerical value in question_id (extract number from q1, q2, etc.)
        question_info['sort_key'] = question_info['question_id'].str.extract(r'(\d+)').astype(int)
        question_info = question_info.sort_values('sort_key').drop('sort_key', axis=1)
        
        # Create pivot table for predictions
        pivot_df = df.pivot_table(
            index=['question_id', 'statement'], 
            columns='religion', 
            values='choice', 
            aggfunc='first'
        ).reset_index()
        
        # Flatten column names and create pred_[1]_<religion> format
        wide_df = question_info.copy()
        
        # Add prediction columns
        for religion in religions:
            col_name = religion.lower()
            if religion in pivot_df.columns:
                # Merge the prediction data
                religion_data = df[df['religion'] == religion][['question_id', 'choice']]
                religion_data = religion_data.rename(columns={'choice': col_name})
                wide_df = wide_df.merge(religion_data, on='question_id', how='left')
            else:
                # Add empty column if religion not found
                wide_df[col_name] = None
        
        # Rename statement column to question_text
        wide_df = wide_df.rename(columns={'statement': 'question_text'})
        
        # Sort by question_id numerically
        wide_df['sort_key'] = wide_df['question_id'].str.extract(r'(\d+)').astype(int)
        wide_df = wide_df.sort_values('sort_key').drop('sort_key', axis=1)
        
        # Generate output filename if not provided
        output_file = str(Path(input_file).parent / "_merged_predictions.csv")
        
        # Save the transformed data
        print(f"💾 Saving transformed data to: {output_file}")
        wide_df.to_csv(output_file, index=False)
        
        # Print summary
        print(f"\n📈 Transformation Summary:")
        print(f"  Input rows: {len(df)}")
        print(f"  Output rows: {len(wide_df)}")
        print(f"  Questions: {len(wide_df)}")  
        print(f"  Religion columns: {len([col for col in wide_df.columns if col not in ['question_id', 'question_text']])}")
        
        # Show first few rows
        print(f"\n🔍 Preview of transformed data:")
        print(wide_df.head().to_string(max_cols=10))
        
        # Show column names
        print(f"\n📋 Column names:")
        for i, col in enumerate(wide_df.columns, 1):
            print(f"  {i:2d}. {col}")
        
        print(f"\n✅ Transformation completed successfully!")
        print(f"📄 Output saved to: {output_file}")
        
        return str(output_file)
        
    except Exception as e:
        print(f"❌ Error during transformation: {e}")
        sys.exit(1)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Transform political compass CSV from long to wide format")
    parser.add_argument("input_file", help="Input CSV file path")
    parser.add_argument("-o", "--output", help="Output CSV file path (optional)")
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input_file).exists():
        print(f"❌ Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Transform the data
    output_file = transform_csv(args.input_file, args.output)
    
if __name__ == "__main__":
    main()
