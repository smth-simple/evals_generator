#!/usr/bin/env python3
"""
Visualization 13: Prompt Category Analysis (Win Rates & Error Rates)
Compares Model A vs Model B performance across different prompt categories.
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import warnings

warnings.filterwarnings('ignore')

def main():
    # ----------------------------
    # 0. Setup Paths
    # ----------------------------
    dataset_path = os.environ.get('DATASET_PATH')
    output_dir = os.environ.get('OUTPUT_DIR')
    
    if not dataset_path: dataset_path = 'evals_data.csv'
    if not output_dir: output_dir = 'viz_output'
    
    output_image_path = os.path.join(output_dir, 'viz_13_prompt_cat_comparison.png')
    output_data_path = os.path.join(output_dir, 'viz_13_data.csv')

    try:
        if not os.path.exists(dataset_path):
            print(f"Error: Dataset not found at {dataset_path}", file=sys.stderr)
            sys.exit(1)
            
        df = pd.read_csv(dataset_path)

        # ----------------------------
        # 1. Prepare Data
        # ----------------------------
        # Ensure we have a prompt category column
        CAT_COL = 'prompt_category'
        if CAT_COL not in df.columns:
            # Fallback: try to find a similar column
            for c in df.columns:
                if 'category' in c.lower() and 'prompt' in c.lower():
                    CAT_COL = c
                    break
        
        if CAT_COL not in df.columns:
            print("Viz 13: 'prompt_category' column not found. Skipping.")
            return

        # Rename models for display
        df['model_display'] = df['model_name'].replace({
            'model_a': 'Base', 'model_b': 'Test',
            'Model A': 'Base', 'Model B': 'Test'
        })

        # Calculate Major Issue Flag if not present
        if 'is_major_issue' not in df.columns:
            def check_major(row):
                metrics = ['instruction_following', 'truthfulness', 'localization', 
                           'writing_style_tone', 'harmlessness']
                for m in metrics:
                    if row.get(m, 3) == 1: return 1
                if row.get('response_length', 0) in [-2, 2]: return 1
                return 0
            df['is_major_issue'] = df.apply(check_major, axis=1)

        # ----------------------------
        # 2. Aggregation
        # ----------------------------
        
        # A. Win Rates per Category
        # We need unique tasks to calculate win rates (since likert is per task, not per model response)
        tasks = df.drop_duplicates(subset=['task_id']).copy()
        
        def calc_win_rates(sub_df):
            total = len(sub_df)
            if total == 0: return pd.Series({'Base Win %': 0, 'Test Win %': 0})
            base_wins = len(sub_df[sub_df['likert'] < 4])
            test_wins = len(sub_df[sub_df['likert'] > 4])
            return pd.Series({
                'Base Win %': (base_wins / total) * 100,
                'Test Win %': (test_wins / total) * 100
            })

        win_stats = tasks.groupby(CAT_COL).apply(calc_win_rates).reset_index()

        # B. Error Rates per Category per Model
        error_stats = df.groupby([CAT_COL, 'model_display'])['is_major_issue'].mean().unstack() * 100
        error_stats = error_stats.rename(columns={'Base': 'Base Error %', 'Test': 'Test Error %'}).reset_index()

        # Merge for data export
        merged = pd.merge(win_stats, error_stats, on=CAT_COL, how='outer').fillna(0)
        
        # Save Data
        os.makedirs(os.path.dirname(output_data_path), exist_ok=True)
        merged.to_csv(output_data_path, index=False)
        print(f"✓ Saved data to: {output_data_path}")

        # ----------------------------
        # 3. Plotting
        # ----------------------------
        categories = merged[CAT_COL].tolist()
        x = np.arange(len(categories))
        width = 0.35

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

        # --- Top Plot: Win Rates ---
        rects1 = ax1.bar(x - width/2, merged['Base Win %'], width, label='Base Model Win Rate', color='#999999', alpha=0.8)
        rects2 = ax1.bar(x + width/2, merged['Test Win %'], width, label='Test Model Win Rate', color='#4A90E2', alpha=0.9)

        ax1.set_ylabel('Win Rate (%)')
        ax1.set_title('Win Rate by Prompt Category', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(axis='y', linestyle='--', alpha=0.3)
        ax1.set_ylim(0, max(merged[['Base Win %', 'Test Win %']].max().max() * 1.15, 50))

        # Add labels
        def autolabel(rects, ax):
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height:.1f}%',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', fontsize=9)
        
        autolabel(rects1, ax1)
        autolabel(rects2, ax1)

        # --- Bottom Plot: Error Rates ---
        rects3 = ax2.bar(x - width/2, merged['Base Error %'], width, label='Base Model Major Error %', color='#666666', alpha=0.6)
        rects4 = ax2.bar(x + width/2, merged['Test Error %'], width, label='Test Model Major Error %', color='#D9534F', alpha=0.9)

        ax2.set_ylabel('Major Error Rate (%)')
        ax2.set_title('Major Error Rate by Prompt Category (Lower is Better)', fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(categories, rotation=45, ha='right')
        ax2.legend()
        ax2.grid(axis='y', linestyle='--', alpha=0.3)
        ax2.set_ylim(0, max(merged[['Base Error %', 'Test Error %']].max().max() * 1.15, 20))

        autolabel(rects3, ax2)
        autolabel(rects4, ax2)

        plt.tight_layout()
        
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        plt.savefig(output_image_path, bbox_inches='tight', dpi=300)
        print(f"✓ Saved image to: {output_image_path}")
        plt.close()

    except Exception as e:
        print(f"Error in viz_13: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()