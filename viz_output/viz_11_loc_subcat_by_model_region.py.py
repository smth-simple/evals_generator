#!/usr/bin/env python3
"""
Visualization 11: Localization Subcategory Breakdown by Model & Region
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
    dataset_path = os.environ.get('DATASET_PATH')
    output_dir = os.environ.get('OUTPUT_DIR')
    if not dataset_path: dataset_path = 'evals_data.csv'
    if not output_dir: output_dir = 'viz_output'
    
    output_image_path = os.path.join(output_dir, 'viz_11_loc_subcat_breakdown.png')
    output_data_path = os.path.join(output_dir, 'viz_11_data.csv')

    try:
        if not os.path.exists(dataset_path):
            print(f"Error: Dataset not found at {dataset_path}", file=sys.stderr)
            sys.exit(1)
            
        df = pd.read_csv(dataset_path)

        # Region Mapping
        lang_to_region = {
            "ja_JP": "East Asia", "ko_KR": "East Asia", "zh_CN": "East Asia", "zh_HK": "East Asia", "zh_TW": "East Asia",
            "hi_IN": "South Asia", "id_ID": "Southeast Asia", "ms_MY": "Southeast Asia", "th_TH": "Southeast Asia", "vi_VN": "Southeast Asia",
            "ar_AE": "MENA", "ar_EG": "MENA", "ar_SA": "MENA", "he_IL": "MENA", "tr_TR": "MENA",
            "fr_FR": "Western Europe", "fr_BE": "Western Europe", "fr_CH": "Western Europe",
            "de_DE": "Western Europe", "de_AT": "Western Europe", "de_CH": "Western Europe",
            "it_IT": "Western Europe", "it_CH": "Western Europe", "es_ES": "Western Europe",
            "pt_PT": "Western Europe", "nl_NL": "Western Europe", "nl_BE": "Western Europe",
            "da_DK": "Nordics", "fi_FI": "Nordics", "no_NO": "Nordics", "sv_SE": "Nordics",
            "pl_PL": "Eastern Europe", "ru_RU": "Eastern Europe", "uk_UA": "Eastern Europe",
            "es_CL": "Latin America", "es_MX": "Latin America", "es_US": "Latin America", "pt_BR": "Latin America",
            "en_US": "North America", "fr_CA": "North America", "en_GB": "Western Europe"
        }
        df["region"] = df["language_code"].map(lang_to_region).fillna("Other")

        # Identify LOC Subcategory Column
        LOC_COL = "loc_subcategory"
        if LOC_COL not in df.columns:
            for c in df.columns:
                if "loc" in c.lower() and "sub" in c.lower(): 
                    LOC_COL = c
                    break
        
        if LOC_COL not in df.columns:
            print("Viz 11: 'loc_subcategory' column not found. Skipping.")
            return

        df['model_display'] = df['model_name'].replace({'model_a': 'Base', 'model_b': 'Test', 'Model A': 'Base', 'Model B': 'Test'})

        # Filter: Only Major LOC Issues (assuming 'loc' == 1)
        # Check if 'loc' column exists, otherwise try 'localization'
        filter_col = 'loc' if 'loc' in df.columns else 'localization'
        if filter_col not in df.columns:
             print("Viz 11: No localization metric column found. Skipping.")
             return

        failures = df[df[filter_col] == 1].copy()
        
        if failures.empty:
            print("Viz 11: No major LOC failures found.")
            return

        failures[LOC_COL] = failures[LOC_COL].fillna("Uncategorized").astype(str)
        
        overall_df = failures.copy()
        overall_df['region'] = 'Overall'
        combined = pd.concat([failures, overall_df], ignore_index=True)

        grouped = combined.groupby(['region', 'model_display', LOC_COL]).size().reset_index(name='count')
        totals = grouped.groupby(['region', 'model_display'])['count'].transform('sum')
        grouped['percentage'] = (grouped['count'] / totals) * 100
        
        os.makedirs(os.path.dirname(output_data_path), exist_ok=True)
        grouped.to_csv(output_data_path, index=False)

        # Plotting
        unique_regions = sorted(grouped['region'].unique())
        if 'Overall' in unique_regions:
            unique_regions.remove('Overall')
            unique_regions.insert(0, 'Overall')
            
        models = ['Base', 'Test']
        subcats = sorted(grouped[LOC_COL].unique())
        colors_list = cm.get_cmap('tab20', len(subcats))
        color_map = {subcat: colors_list(i) for i, subcat in enumerate(subcats)}

        n_regions = len(unique_regions)
        cols = min(n_regions, 3)
        rows = (n_regions + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows + 1), sharey=True)
        axes = axes.flatten() if n_regions > 1 else [axes]

        for i, region in enumerate(unique_regions):
            ax = axes[i]
            region_data = grouped[grouped['region'] == region]
            bottoms = {m: 0 for m in models}
            
            for subcat in subcats:
                vals = []
                for m in models:
                    row = region_data[(region_data['model_display'] == m) & (region_data[LOC_COL] == subcat)]
                    vals.append(row['percentage'].values[0] if not row.empty else 0)
                ax.bar(models, vals, bottom=[bottoms[m] for m in models], label=subcat if i == 0 else "", color=color_map[subcat], alpha=0.9, width=0.6)
                for j, m in enumerate(models): bottoms[m] += vals[j]

            for m_idx, m in enumerate(models):
                total_count = region_data[region_data['model_display'] == m]['count'].sum()
                if total_count > 0:
                    ax.text(m_idx, 102, f"n={total_count}", ha='center', va='bottom', fontsize=10, fontweight='bold', color='black')

            ax.set_title(region, fontsize=12, fontweight='bold')
            ax.set_ylim(0, 115)
            if i % cols == 0: ax.set_ylabel("% of LOC Failures")
            ax.grid(axis='y', linestyle='--', alpha=0.3)

        for j in range(i + 1, len(axes)): axes[j].axis('off')

        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.92), ncol=min(len(subcats), 4), title="Localization Subcategory", frameon=True)

        plt.tight_layout()
        plt.subplots_adjust(top=0.90)
        
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        plt.savefig(output_image_path, bbox_inches='tight', dpi=300)
        print(f"✓ Saved image to: {output_image_path}")
        plt.close()

    except Exception as e:
        print(f"Error in viz_11: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()