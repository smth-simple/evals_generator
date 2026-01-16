#!/usr/bin/env python3
"""
Visualization 19: Top 8 Languages with Highest Response Length Disparity
Focusses on the languages where the Test and Base models differ most in length tendency.
"""
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
    output_image_path = os.path.join(output_dir, 'viz_19_rl_disparity_top_langs.png')
    output_data_path = os.path.join(output_dir, 'viz_19_data.csv')
    
    try:
        if not os.path.exists(dataset_path):
            print(f"Error: Dataset not found at {dataset_path}")
            return
        df = pd.read_csv(dataset_path)

        # 1. Prepare Data
        df['model_display'] = df['model_name'].replace({'model_a': 'Base', 'model_b': 'Test'})
        
        # 2. Calculate RL Metrics per Language and Model
        # Scores: -2, -1, 0, 1, 2
        rl_stats = df.groupby(['language_code', 'model_display', 'response_length']).size().unstack(fill_value=0)
        
        # Ensure all columns exist
        for col in [-2, -1, 0, 1, 2]:
            if col not in rl_stats.columns:
                rl_stats[col] = 0
        
        # Normalize to percentages
        rl_pcts = rl_stats.div(rl_stats.sum(axis=1), axis=0) * 100
        
        # Calculate Net Length Bias: (% Long) - (% Short)
        def calc_bias(row):
            long_pct = row.get(1, 0) + row.get(2, 0)
            short_pct = row.get(-1, 0) + row.get(-2, 0)
            return long_pct - short_pct

        bias_series = rl_pcts.apply(calc_bias, axis=1)
        bias_df = bias_series.unstack()
        
        # Calculate Absolute Difference between Test and Base
        if 'Test' in bias_df.columns and 'Base' in bias_df.columns:
            bias_df['Abs_Delta'] = (bias_df['Test'] - bias_df['Base']).abs()
        else:
            print("Error: Missing model data for comparison.")
            return

        # 3. Identify Top 8 Languages
        top_8_langs = bias_df.sort_values('Abs_Delta', ascending=False).head(8).index.tolist()
        
        # Filter pcts for these top 8
        final_pcts = rl_pcts.loc[top_8_langs]
        
        # Save Data for the top 8
        os.makedirs(os.path.dirname(output_data_path), exist_ok=True)
        final_pcts.to_csv(output_data_path)
        print(f"✓ Saved top 8 language RL data to: {output_data_path}")

        # 4. Plotting (Diverging Stacked Bars)
        fig, ax = plt.subplots(figsize=(12, 10))
        
        colors = {
            -2: '#b2182b', # Major Short
            -1: '#ef8a62', # Minor Short
             0: '#f7f7f7', # Just Right
             1: '#67a9cf', # Minor Long
             2: '#2166ac'  # Major Long
        }
        
        y_ticks = []
        y_labels = []
        
        curr_y = 0
        for lang in top_8_langs:
            for model in ['Base', 'Test']:
                if (lang, model) not in final_pcts.index: continue
                
                row = final_pcts.loc[(lang, model)]
                
                # Center line logic (Diverging)
                center_offset = -(row[0]/2 + row[-1] + row[-2])
                
                left = center_offset
                for score in [-2, -1, 0, 1, 2]:
                    width = row[score]
                    ax.barh(curr_y, width, left=left, color=colors[score], edgecolor='black', linewidth=0.3)
                    
                    if width > 6 and score != 0:
                        txt_color = 'white' if abs(score) == 2 else 'black'
                        ax.text(left + width/2, curr_y, f"{width:.0f}%", va='center', ha='center', 
                                fontsize=9, fontweight='bold', color=txt_color)
                    left += width
                
                y_ticks.append(curr_y)
                y_labels.append(f"{lang}\n({model})")
                curr_y += 1
            curr_y += 0.6 # Gap between languages

        ax.axvline(0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels, fontsize=10)
        ax.set_title("Response Length Disparity: Top 8 Most Divergent Languages\n(Too Short ← vs. → Too Long)", 
                     fontsize=14, fontweight='bold', pad=45)
        ax.set_xlabel("Percentage Deviation from 'Just Right' (%)")
        
        # Legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color=colors[-2], lw=4, label='Major Short (-2)'),
            Line2D([0], [0], color=colors[-1], lw=4, label='Minor Short (-1)'),
            Line2D([0], [0], color=colors[0], lw=4, label='Just Right (0)'),
            Line2D([0], [0], color=colors[1], lw=4, label='Minor Long (+1)'),
            Line2D([0], [0], color=colors[2], lw=4, label='Major Long (+2)')
        ]
        ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.08), 
                  ncol=5, frameon=False)

        plt.tight_layout()
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
        print(f"✓ Top 8 RL Disparity Visual Saved: {output_image_path}")
        plt.close()

    except Exception as e:
        print(f"Error viz_19: {e}")

if __name__ == "__main__":
    main()