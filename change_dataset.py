#!/usr/bin/env python3
"""
Quick utility to change the dataset path in configuration files
"""

import json
import sys
from pathlib import Path

def update_dataset_path(new_path):
    """Update dataset path in both configuration files"""
    
    # Update dataset_config.json
    config_file = 'dataset_config.json'
    if Path(config_file).exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        old_path = config.get('dataset_path', 'unknown')
        config['dataset_path'] = new_path
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Updated {config_file}")
        print(f"  Old path: {old_path}")
        print(f"  New path: {new_path}")
    else:
        print(f"⚠️  {config_file} not found")
    
    # Update evals_report_config.json
    config_file = 'evals_report_config.json'
    if Path(config_file).exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        config['dataset_path'] = new_path
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Updated {config_file}")
    else:
        print(f"⚠️  {config_file} not found")
    
    # Check if file exists
    print()
    if Path(new_path).exists():
        file_size = Path(new_path).stat().st_size / (1024 * 1024)
        print(f"✓ Dataset file found: {new_path} ({file_size:.2f} MB)")
    else:
        print(f"⚠️  Warning: File not found at {new_path}")
        print(f"   Make sure to place your CSV file at this location before generating reports")

def main():
    print("\n" + "=" * 70)
    print("DATASET PATH UPDATER")
    print("=" * 70 + "\n")
    
    if len(sys.argv) < 2:
        print("Usage: python change_dataset.py <path-to-csv-file>")
        print("\nExamples:")
        print("  python change_dataset.py my_data.csv")
        print("  python change_dataset.py data/evals_combined.csv")
        print("  python change_dataset.py /full/path/to/evals.csv")
        print()
        
        # Show current dataset
        try:
            with open('dataset_config.json', 'r') as f:
                config = json.load(f)
                current = config.get('dataset_path', 'not configured')
                print(f"Current dataset path: {current}")
                if Path(current).exists():
                    file_size = Path(current).stat().st_size / (1024 * 1024)
                    print(f"File found: {file_size:.2f} MB")
                else:
                    print(f"File not found at this location")
        except:
            print("No configuration found")
        
        print()
        sys.exit(1)
    
    new_path = sys.argv[1]
    
    print(f"Updating dataset path to: {new_path}\n")
    update_dataset_path(new_path)
    
    print("\n" + "=" * 70)
    print("DONE!")
    print("=" * 70)
    print("\nYou can now generate reports with:")
    print("  python report_generator.py --config evals_report_config.json")
    print()

if __name__ == "__main__":
    main()
