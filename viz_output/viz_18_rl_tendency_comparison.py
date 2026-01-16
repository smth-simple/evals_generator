#!/usr/bin/env python3
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import warnings

warnings.filterwarnings('ignore')

def main():
    dataset_path = os.environ.get('DATASET_PATH', 'evals_data.csv')
    output_dir = os.environ.get('OUTPUT_DIR', 'viz_output')
    output_image_path = os.path.join(output_dir, 'viz_18_rl_tendency.png')
    output_data_path = os.path.join(output_dir, 'viz_18_data.csv')
    
    try:
        if not os.path.exists(dataset_path): return
        df = pd.read_csv(dataset_path)

        lang_to_region = {"ja_JP": "East Asia", "ko_KR": "East Asia", "zh_CN": "East Asia", "zh_HK": "East Asia", "zh_TW": "East Asia", "hi_IN": "South Asia", "id_ID": "Southeast Asia", "ms_MY": "Southeast Asia", "th_TH": "Southeast Asia", "vi_VN": "Southeast Asia", "ar_AE": "MENA", "ar_EG": "MENA", "ar_SA": "MENA", "he_IL": "MENA", "tr_TR": "MENA", "fr_FR": "Western Europe", "fr_BE": "Western Europe", "fr_CH": "Western Europe", "de_DE": "Western Europe", "de_AT": "Western Europe", "de_CH": "Western Europe", "it_IT": "Western Europe", "it_CH": "Western Europe", "es_ES": "Western Europe", "pt_PT": "Western Europe", "nl_NL": "Western Europe", "nl_BE": "Western Europe", "da_DK": "Nordics", "fi_FI": "Nordics", "no_NO": "Nordics", "sv_SE": "Nordics", "pl_PL": "Eastern Europe", "ru_RU": "Eastern Europe", "uk_UA": "Eastern Europe", "es_CL": "Latin America", "es_MX": "Latin America", "es_US": "Latin America", "pt_BR": "Latin America", "en_US": "North America", "fr_CA": "North America", "en_GB": "Western Europe"}
        df['region'] = df['language_code'].map(lang_to_region).fillna("Other")
        df['model_display'] = df['model_name'].replace({'model_a': 'Base', 'model_b': 'Test'})

        rl_counts = df.groupby(['region', 'model_display', 'response_length']).size().unstack(fill_value=0)
        overall = df.groupby(['model_display', 'response_length']).size().unstack(fill_value=0)
        overall.index = pd.MultiIndex.from_tuples([('OVERALL', m) for m in overall.index], names=['region', 'model_display'])
        combined = pd.concat([rl_counts, overall])
        pcts = combined.div(combined.sum(axis=1), axis=0) * 100

        # --- SAVE DATA ---
        os.makedirs(os.path.dirname(output_data_path), exist_ok=True)
        pcts.to_csv(output_data_path)
        print(f"✓ Saved data to: {output_data_path}")

        # --- PLOT IMAGE ---
        regions = ['OVERALL'] + sorted([r for r in df['region'].unique() if r != 'Other'])
        models = ['Base', 'Test']
        colors = {-2: '#b2182b', -1: '#ef8a62', 0: '#f7f7f7', 1: '#67a9cf', 2: '#2166ac'}
        
        fig, ax = plt.subplots(figsize=(12, len(regions) * 1.2 + 2))
        curr_y = 0
        y_ticks, y_labels = [], []
        for region in regions:
            for model in models:
                if (region, model) not in pcts.index: continue
                row = pcts.loc[(region, model)]
                center_offset = -(row.get(0,0)/2 + row.get(-1,0) + row.get(-2,0))
                left = center_offset
                for score in [-2, -1, 0, 1, 2]:
                    width = row.get(score, 0)
                    ax.barh(curr_y, width, left=left, color=colors[score], edgecolor='black', linewidth=0.3)
                    if width > 5 and score != 0:
                        ax.text(left + width/2, curr_y, f"{width:.0f}%", va='center', ha='center', fontsize=8, fontweight='bold', color='white' if abs(score)==2 else 'black')
                    left += width
                y_ticks.append(curr_y); y_labels.append(f"{region}\n({model})")
                curr_y += 1
            curr_y += 0.5

        ax.axvline(0, color='black', linewidth=1.5, alpha=0.7)
        ax.set_yticks(y_ticks); ax.set_yticklabels(y_labels)
        ax.set_title("Response Length Tendency", fontsize=14, fontweight='bold', pad=40)
        legend_elements = [Line2D([0], [0], color=colors[s], lw=4, label=f'RL {s}') for s in [-2, -1, 0, 1, 2]]
        ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=5, frameon=False)
        plt.tight_layout(); plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved image to: {output_image_path}")
        plt.close()
    except Exception as e: print(f"Error viz_18: {e}")

if __name__ == "__main__": main()