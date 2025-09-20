#!/usr/bin/env python3
"""
JSON to CSV Converter - Convert political compass scores from JSON to CSV
Converts the PC scores JSON file to a CSV with religion, econ_score, soc_score columns.
"""

import json
import csv
import argparse
import sys
from pathlib import Path
from typing import Optional

def json_to_csv(input_file: str, output_file: Optional[str] = None):
    """
    Convert JSON file to CSV format
    
    Args:
        input_file: Path to the input JSON file
        output_file: Path for output CSV (optional, auto-generated if not provided)
    """
    
    try:
        # Read the JSON file
        print(f"📖 Reading JSON file: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Loaded {len(data)} records")
        
        # Generate output filename if not provided
        if output_file is None:
            input_path = Path(input_file)
            output_file = str(input_path.parent / f"{input_path.stem}.csv")
        
        # Convert to CSV
        print(f"🔄 Converting to CSV format...")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['religion', 'econ_score', 'soc_score']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write data rows
            for record in data:
                writer.writerow({
                    'religion': record['responder'],
                    'econ_score': record['econ_score'],
                    'soc_score': record['soc_score']
                })
        
        print(f"💾 CSV saved to: {output_file}")
        
        # Show preview
        print(f"\n🔍 Preview of CSV data:")
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:6]):  # Show header + first 5 rows
                print(f"  {line.strip()}")
            if len(lines) > 6:
                print(f"  ... and {len(lines) - 6} more rows")
        
        print(f"\n✅ Conversion completed successfully!")
        print(f"📊 Total records: {len(data)}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        sys.exit(1)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Convert political compass scores JSON to CSV")
    parser.add_argument("input_file", help="Input JSON file path")
    parser.add_argument("-o", "--output", help="Output CSV file path (optional)")
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input_file).exists():
        print(f"❌ Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Convert the data
    json_to_csv(args.input_file, args.output)
    
if __name__ == "__main__":
    main()