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
    output_image_path = os.path.join(output_dir, 'viz_15_minor_error_deltas.png')
    output_data_path = os.path.join(output_dir, 'viz_15_data.csv')
    
    try:
        if not os.path.exists(dataset_path): return
        df = pd.read_csv(dataset_path)
        
        metrics = {
            'IF_Minor': lambda x: x['instruction_following'] == 2,
            'TF_Minor': lambda x: x['truthfulness'] == 2,
            'LOC_Minor': lambda x: x.get('loc', x.get('localization')) == 2,
            'Style_Minor': lambda x: x.get('writing_style_tone', x.get('style')) == 2,
            'RL_Minor': lambda x: x['response_length'].isin([-1, 1])
        }
        
        for name, func in metrics.items():
            df[name] = func(df)

        df['model_display'] = df['model_name'].replace({'model_a': 'Base', 'model_b': 'Test'})
        agg = df.groupby(['language_code', 'model_display'])[list(metrics.keys())].mean().reset_index()
        pivot = agg.pivot(index='language_code', columns='model_display')
        
        summary = pd.DataFrame(index=pivot.index)
        for col in metrics.keys():
            if (col, 'Test') in pivot.columns:
                summary[f"{col}_delta"] = (pivot[(col, 'Test')] - pivot[(col, 'Base')]) * 100
        
        # --- SAVE DATA ---
        os.makedirs(os.path.dirname(output_data_path), exist_ok=True)
        summary.to_csv(output_data_path)
        print(f"✓ Saved data to: {output_data_path}")

        # --- PLOT IMAGE ---
        summary['Total_Minor_Delta'] = summary.sum(axis=1)
        summary = summary.sort_values('Total_Minor_Delta')
        metrics_to_plot = [c for c in summary.columns if 'delta' in c]
        
        fig, ax = plt.subplots(figsize=(12, len(summary) * 0.6 + 2))
        data = summary[metrics_to_plot].values
        im = ax.imshow(data, aspect='auto', cmap='RdBu_r', vmin=-10, vmax=10)
        
        ax.set_yticks(np.arange(len(summary)))
        ax.set_yticklabels(summary.index)
        ax.set_xticks(np.arange(len(metrics_to_plot)))
        ax.set_xticklabels([m.replace('_delta', '') for m in metrics_to_plot], rotation=45, ha='right')
        
        for i in range(len(summary)):
            for j in range(len(metrics_to_plot)):
                val = data[i, j]
                color = "white" if abs(val) > 5 else "black"
                ax.text(j, i, f"{val:.1f}", ha="center", va="center", color=color, fontsize=9)
                
        ax.set_title("Minor Error Rate Deltas (Blue = Test Model is Better)", fontweight='bold')
        plt.colorbar(im, label="Percentage Point Difference")
        plt.tight_layout()
        plt.savefig(output_image_path, dpi=300)
        print(f"✓ Saved image to: {output_image_path}")
        plt.close()
    except Exception as e: print(f"Error viz_15: {e}")

if __name__ == "__main__": main()