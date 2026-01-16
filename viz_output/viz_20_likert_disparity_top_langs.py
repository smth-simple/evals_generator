#!/usr/bin/env python3
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

def main():
    dataset_path = os.environ.get('DATASET_PATH', 'evals_data.csv')
    output_dir = os.environ.get('OUTPUT_DIR', 'viz_output')
    output_image_path = os.path.join(output_dir, 'viz_20_likert_disparity_top_langs.png')
    output_data_path = os.path.join(output_dir, 'viz_20_data.csv')
    
    try:
        if not os.path.exists(dataset_path): return
        df = pd.read_csv(dataset_path)
        tasks = df.drop_duplicates(subset=['task_id']).copy()
        tasks['likert'] = pd.to_numeric(tasks['likert'], errors='coerce')
        tasks = tasks.dropna(subset=['likert']).astype({'likert': int})

        def calc_win_metrics(group):
            total = len(group)
            base_rate = (group['likert'] < 4).sum() / total * 100
            test_rate = (group['likert'] > 4).sum() / total * 100
            return pd.Series({'Base_Win_Rate': base_rate, 'Test_Win_Rate': test_rate, 'Abs_Delta': abs(test_rate - base_rate)})

        lang_metrics = tasks.groupby('language_code').apply(calc_win_metrics)
        top_8_langs = lang_metrics.sort_values('Abs_Delta', ascending=False).head(8).index.tolist()
        subset = tasks[tasks['language_code'].isin(top_8_langs)].copy()
        overall_data = tasks.copy(); overall_data['language_code'] = 'OVERALL'
        combined = pd.concat([overall_data, subset], ignore_index=True)
        dist_pct = combined.groupby(['language_code', 'likert']).size().unstack(fill_value=0).div(combined.groupby('language_code').size(), axis=0) * 100
        
        # --- SAVE DATA ---
        os.makedirs(os.path.dirname(output_data_path), exist_ok=True)
        dist_pct.to_csv(output_data_path)
        print(f"✓ Saved data to: {output_data_path}")

        # --- PLOT IMAGE ---
        ordered_rows = ['OVERALL'] + top_8_langs
        dist_pct = dist_pct.reindex(ordered_rows)
        fig, ax = plt.subplots(figsize=(14, len(ordered_rows) * 0.8 + 4))
        colors = {1: '#b2182b', 2: '#d6604d', 3: '#f4a582', 4: '#e0e0e0', 5: '#92c5de', 6: '#4393c3', 7: '#2166ac'}
        left = np.zeros(len(dist_pct))
        for score in range(1, 8):
            widths = dist_pct.get(score, 0)
            ax.barh(dist_pct.index, widths, left=left, label=f"Score {score}", color=colors[score], edgecolor='white', linewidth=0.5)
            for i, width in enumerate(widths):
                if width > 4: ax.text(left[i] + width/2, i, f"{width:.0f}%", va='center', ha='center', fontsize=9, color='white' if score in [1, 2, 6, 7] else 'black', fontweight='bold')
            left += widths

        ax.set_title("User Preference Disparity: Top 8 Most Divergent Languages", fontsize=16, fontweight='bold', pad=30)
        ax.invert_yaxis()
        handles, labels = ax.get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.98), ncol=7, frameon=False)
        plt.subplots_adjust(top=0.82); plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved image to: {output_image_path}")
        plt.close()
    except Exception as e: print(f"Error viz_20: {e}")

if __name__ == "__main__": main()