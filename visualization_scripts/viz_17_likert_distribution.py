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
    output_image_path = os.path.join(output_dir, 'viz_17_likert_distribution.png')
    output_data_path = os.path.join(output_dir, 'viz_17_data.csv')
    
    try:
        if not os.path.exists(dataset_path): return
        df = pd.read_csv(dataset_path)

        lang_to_region = {"ja_JP": "East Asia", "ko_KR": "East Asia", "zh_CN": "East Asia", "zh_HK": "East Asia", "zh_TW": "East Asia", "hi_IN": "South Asia", "id_ID": "Southeast Asia", "ms_MY": "Southeast Asia", "th_TH": "Southeast Asia", "vi_VN": "Southeast Asia", "ar_AE": "MENA", "ar_EG": "MENA", "ar_SA": "MENA", "he_IL": "MENA", "tr_TR": "MENA", "fr_FR": "Western Europe", "fr_BE": "Western Europe", "fr_CH": "Western Europe", "de_DE": "Western Europe", "de_AT": "Western Europe", "de_CH": "Western Europe", "it_IT": "Western Europe", "it_CH": "Western Europe", "es_ES": "Western Europe", "pt_PT": "Western Europe", "nl_NL": "Western Europe", "nl_BE": "Western Europe", "da_DK": "Nordics", "fi_FI": "Nordics", "no_NO": "Nordics", "sv_SE": "Nordics", "pl_PL": "Eastern Europe", "ru_RU": "Eastern Europe", "uk_UA": "Eastern Europe", "es_CL": "Latin America", "es_MX": "Latin America", "es_US": "Latin America", "pt_BR": "Latin America", "en_US": "North America", "fr_CA": "North America", "en_GB": "Western Europe"}
        
        tasks = df.drop_duplicates(subset=['task_id']).copy()
        tasks['region'] = tasks['language_code'].map(lang_to_region).fillna("Other")
        overall_tasks = tasks.copy(); overall_tasks['region'] = 'OVERALL'
        combined = pd.concat([tasks, overall_tasks], ignore_index=True)

        combined['likert'] = pd.to_numeric(combined['likert'], errors='coerce')
        combined = combined.dropna(subset=['likert'])
        combined['likert'] = combined['likert'].astype(int)
        
        dist = combined.groupby(['region', 'likert']).size().unstack(fill_value=0)
        dist_pct = dist.div(dist.sum(axis=1), axis=0) * 100
        
        # --- SAVE DATA ---
        os.makedirs(os.path.dirname(output_data_path), exist_ok=True)
        dist_pct.to_csv(output_data_path)
        print(f"✓ Saved data to: {output_data_path}")

        # --- PLOT IMAGE ---
        regions_ordered = ['OVERALL'] + sorted([r for r in dist_pct.index if r != 'OVERALL'])
        dist_pct = dist_pct.reindex(regions_ordered)

        fig, ax = plt.subplots(figsize=(14, len(regions_ordered) * 0.8 + 3))
        colors = {1: '#b2182b', 2: '#d6604d', 3: '#f4a582', 4: '#e0e0e0', 5: '#92c5de', 6: '#4393c3', 7: '#2166ac'}
        
        left = np.zeros(len(dist_pct))
        for score in range(1, 8):
            widths = dist_pct[score].values
            ax.barh(dist_pct.index, widths, left=left, label=f"Score {score}", color=colors[score], edgecolor='white', linewidth=0.5)
            for i, width in enumerate(widths):
                if width > 4: ax.text(left[i] + width/2, i, f"{width:.0f}%", va='center', ha='center', fontsize=9, color='white' if score in [1, 2, 6, 7] else 'black', fontweight='bold')
            left += widths

        ax.set_title("Likert Intensity by Region", fontsize=16, fontweight='bold', pad=45)
        ax.invert_yaxis()
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=7, frameon=False)
        plt.tight_layout(rect=[0, 0, 1, 0.95]); plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved image to: {output_image_path}")
        plt.close()
    except Exception as e: print(f"Error viz_17: {e}")

if __name__ == "__main__": main()