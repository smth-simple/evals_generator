#!/usr/bin/env python3
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import warnings

warnings.filterwarnings('ignore')

def main():
    dataset_path = os.environ.get('DATASET_PATH', 'evals_data.csv')
    output_dir = os.environ.get('OUTPUT_DIR', 'viz_output')
    output_image_path = os.path.join(output_dir, 'viz_16_composite_score.png')
    output_data_path = os.path.join(output_dir, 'viz_16_data.csv')
    
    try:
        if not os.path.exists(dataset_path): return
        df = pd.read_csv(dataset_path)
        
        def score_map(x): return {3: 100, 2: 50, 1: 0}.get(x, np.nan)
        def rl_map(x):
            if x == 0: return 100
            elif abs(x) == 1: return 50
            elif abs(x) == 2: return 0
            return np.nan

        metric_map = {'instruction_following': 'IF', 'truthfulness': 'TF', 'loc': 'LOC', 'localization': 'LOC', 'writing_style_tone': 'Style', 'style': 'Style', 'harmlessness': 'Harm', 'response_length': 'RL'}
        cols_to_use = []
        for col, label in metric_map.items():
            if col in df.columns and label not in [m[1] for m in cols_to_use]:
                cols_to_use.append((col, label))
        
        score_data = []
        for orig_col, label in cols_to_use:
            score_col = f"Score_{label}"
            df[score_col] = df[orig_col].apply(rl_map if label == 'RL' else score_map)
            score_data.append(score_col)
            
        df['model_display'] = df['model_name'].replace({'model_a': 'Base', 'model_b': 'Test'})
        lang_scores = df.groupby(['language_code', 'model_display'])[score_data].mean().unstack()
        
        num_metrics = len(score_data)
        deltas = pd.DataFrame(index=lang_scores.index)
        for col in score_data:
            label = col.replace('Score_', '')
            deltas[label] = (lang_scores[(col, 'Test')] - lang_scores[(col, 'Base')]) / num_metrics
            
        deltas['Total_Delta'] = deltas.sum(axis=1)
        
        # --- SAVE DATA ---
        os.makedirs(os.path.dirname(output_data_path), exist_ok=True)
        deltas.to_csv(output_data_path)
        print(f"✓ Saved data to: {output_data_path}")

        # --- PLOT IMAGE ---
        deltas = deltas.sort_values('Total_Delta')
        fig, ax = plt.subplots(figsize=(12, len(deltas) * 0.5 + 3))
        categories = [c for c in deltas.columns if c != 'Total_Delta']
        colors = cm.get_cmap('tab10', len(categories))
        
        y_pos = np.arange(len(deltas))
        lefts = np.zeros(len(deltas))
        for i, cat in enumerate(categories):
            widths = deltas[cat].values
            ax.barh(y_pos, widths, left=lefts, color=colors(i), label=cat, edgecolor='white', linewidth=0.5)
            lefts += widths
            
        for i, total in enumerate(deltas['Total_Delta']):
            ax.text(total + (0.5 if total >= 0 else -0.5), i, f"{total:.1f}", va='center', ha='left' if total >= 0 else 'right', fontsize=9, fontweight='bold')

        ax.axvline(0, color='black', linewidth=1.0, alpha=0.7)
        ax.set_yticks(y_pos); ax.set_yticklabels(deltas.index)
        ax.set_title("Composite Quality Score Delta (Segmented)", fontweight='bold', pad=25)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=num_metrics, frameon=False)
        plt.tight_layout(); plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved image to: {output_image_path}")
        plt.close()
    except Exception as e: print(f"Error viz_16: {e}")

if __name__ == "__main__": main()