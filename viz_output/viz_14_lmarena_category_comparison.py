#!/usr/bin/env python3
"""
Visualization 14: LMArena Category Comparison (Hard, Long, Complex, Expert)
Filters for positive instances (excluding 'Not ...') and compares Win/Error rates.
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

def main():
    # ----------------------------
    # 0. Setup Paths
    # ----------------------------
    dataset_path = os.environ.get('DATASET_PATH')
    output_dir = os.environ.get('OUTPUT_DIR')
    
    # Defaults for manual testing
    if not dataset_path: dataset_path = 'evals_data.csv'
    if not output_dir: output_dir = 'viz_output'
    
    output_image_path = os.path.join(output_dir, 'viz_14_lmarena_category_comparison.png')
    output_data_path = os.path.join(output_dir, 'viz_14_data.csv')

    try:
        if not os.path.exists(dataset_path):
            print(f"Error: Dataset not found at {dataset_path}", file=sys.stderr)
            sys.exit(1)
            
        df = pd.read_csv(dataset_path)

        # ----------------------------
        # 1. Prepare Data
        # ----------------------------
        # Rename models for display
        df['model_display'] = df['model_name'].replace({
            'model_a': 'Base', 'model_b': 'Test',
            'Model A': 'Base', 'Model B': 'Test'
        })

        # Ensure Major Issue Flag exists
        if 'is_major_issue' not in df.columns:
            def check_major(row):
                metrics = ['instruction_following', 'truthfulness', 'localization', 
                           'writing_style_tone', 'harmlessness']
                for m in metrics:
                    if row.get(m, 3) == 1: return 1
                if row.get('response_length', 0) in [-2, 2]: return 1
                return 0
            df['is_major_issue'] = df.apply(check_major, axis=1)

        # CORRECTED COLUMN MAPPING
        # (Column Name in CSV, Display Label on Chart)
        target_cols = [
            ('Hard Prompts', 'Hard Prompts'),
            ('Longer queries', 'Longer Queries'),
            ('Instruction following (prompt complexity)', 'Complex Prompts (IF)'),
            ('Expert prompt', 'Expert Prompts')
        ]

        # ----------------------------
        # 2. Aggregation Loop
        # ----------------------------
        results = []

        for col, label in target_cols:
            # Check if column exists
            if col not in df.columns:
                # fuzzy match check (case insensitive) just in case
                found = False
                for c in df.columns:
                    if c.lower() == col.lower():
                        col = c
                        found = True
                        break
                if not found:
                    print(f"Viz 14: Column '{col}' not found. Skipping.")
                    continue

            # FILTER LOGIC: Exclude values starting with "Not" (and handle NaNs)
            # e.g., Keep "Hard Prompt", exclude "Not Hard Prompt"
            subset = df[
                df[col].notna() & 
                (~df[col].astype(str).str.startswith('Not'))
            ].copy()

            if subset.empty:
                print(f"Viz 14: No positive data found for '{col}'. Skipping.")
                continue

            # A. Win Rates (Task Level)
            tasks = subset.drop_duplicates(subset=['task_id'])
            total_tasks = len(tasks)
            
            if total_tasks > 0:
                base_wins = len(tasks[tasks['likert'] < 4])
                test_wins = len(tasks[tasks['likert'] > 4])
                base_win_rate = (base_wins / total_tasks) * 100
                test_win_rate = (test_wins / total_tasks) * 100
            else:
                base_win_rate = 0
                test_win_rate = 0

            # B. Error Rates (Model Level)
            base_errors = subset[subset['model_display'] == 'Base']['is_major_issue'].mean() * 100
            test_errors = subset[subset['model_display'] == 'Test']['is_major_issue'].mean() * 100

            results.append({
                'Category': label,
                'Base Win %': base_win_rate,
                'Test Win %': test_win_rate,
                'Base Error %': base_errors,
                'Test Error %': test_errors,
                'Count': total_tasks
            })

        if not results:
            print("Viz 14: No data extracted for LMArena categories.")
            return

        summary = pd.DataFrame(results)
        
        # Save Data
        os.makedirs(os.path.dirname(output_data_path), exist_ok=True)
        summary.to_csv(output_data_path, index=False)
        print(f"✓ Saved data to: {output_data_path}")

        # ----------------------------
        # 3. Plotting
        # ----------------------------
        categories = summary['Category'].tolist()
        x = np.arange(len(categories))
        width = 0.35

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)

        # --- Top Panel: Win Rates ---
        rects1 = ax1.bar(x - width/2, summary['Base Win %'], width, label='Base Model', color='#999999', alpha=0.8)
        rects2 = ax1.bar(x + width/2, summary['Test Win %'], width, label='Test Model', color='#4A90E2', alpha=0.9)

        ax1.set_ylabel('Win Rate (%)')
        ax1.set_title('Win Rate by LMArena Category', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper right')
        ax1.grid(axis='y', linestyle='--', alpha=0.3)
        
        # Dynamic Y-Limit padding
        max_win = summary[['Base Win %', 'Test Win %']].max().max()
        ax1.set_ylim(0, max(max_win * 1.15, 50))

        # Add Labels
        def autolabel(rects, ax):
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height:.1f}%',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        autolabel(rects1, ax1)
        autolabel(rects2, ax1)

        # --- Bottom Panel: Error Rates ---
        rects3 = ax2.bar(x - width/2, summary['Base Error %'], width, label='Base Model', color='#666666', alpha=0.6)
        rects4 = ax2.bar(x + width/2, summary['Test Error %'], width, label='Test Model', color='#D9534F', alpha=0.9)

        ax2.set_ylabel('Major Error Rate (%)')
        ax2.set_title('Major Error Rate (Lower is Better)', fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(categories, rotation=0, fontsize=11)
        ax2.legend(loc='upper right')
        ax2.grid(axis='y', linestyle='--', alpha=0.3)
        
        max_err = summary[['Base Error %', 'Test Error %']].max().max()
        ax2.set_ylim(0, max(max_err * 1.15, 20))

        autolabel(rects3, ax2)
        autolabel(rects4, ax2)

        # Add "n=" counts at the bottom
        for i, count in enumerate(summary['Count']):
            ax2.text(i, -max_err*0.15, f"(n={count})", ha='center', fontsize=10, color='gray')

        plt.tight_layout()
        
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        plt.savefig(output_image_path, bbox_inches='tight', dpi=300)
        print(f"✓ Saved image to: {output_image_path}")
        plt.close()

    except Exception as e:
        print(f"Error in viz_14: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()