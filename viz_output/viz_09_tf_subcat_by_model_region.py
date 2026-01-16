#!/usr/bin/env python3
"""
Visualization 9: Truthfulness Subcategory Breakdown by Model & Region (with Counts)
Generates a faceted stacked bar chart comparing Model A vs Model B side-by-side.
Includes 'Overall' view and error counts on top of bars.
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
    
    # Defaults for manual testing
    if not dataset_path: dataset_path = 'evals_data.csv'
    if not output_dir: output_dir = 'viz_output'
    
    output_image_path = os.path.join(output_dir, 'viz_09_tf_subcat_breakdown.png')
    output_data_path = os.path.join(output_dir, 'viz_09_data.csv')

    try:
        if not os.path.exists(dataset_path):
            print(f"Error: Dataset not found at {dataset_path}", file=sys.stderr)
            sys.exit(1)
            
        df = pd.read_csv(dataset_path)

        # ----------------------------
        # 1. Prepare Data
        # ----------------------------
        # Region Mapping
        lang_to_region = {
            "ja_JP": "East Asia", "ko_KR": "East Asia", "zh_CN": "East Asia", "zh_HK": "East Asia", "zh_TW": "East Asia",
            "hi_IN": "South Asia",
            "id_ID": "Southeast Asia", "ms_MY": "Southeast Asia", "th_TH": "Southeast Asia", "vi_VN": "Southeast Asia",
            "ar_AE": "MENA", "ar_EG": "MENA", "ar_SA": "MENA", "he_IL": "MENA", "tr_TR": "MENA",
            "fr_FR": "Western Europe", "fr_BE": "Western Europe", "fr_CH": "Western Europe",
            "de_DE": "Western Europe", "de_AT": "Western Europe", "de_CH": "Western Europe",
            "it_IT": "Western Europe", "it_CH": "Western Europe", "es_ES": "Western Europe",
            "pt_PT": "Western Europe", "nl_NL": "Western Europe", "nl_BE": "Western Europe",
            "da_DK": "Nordics", "fi_FI": "Nordics", "no_NO": "Nordics", "sv_SE": "Nordics",
            "pl_PL": "Eastern Europe", "ru_RU": "Eastern Europe", "uk_UA": "Eastern Europe",
            "es_CL": "Latin America", "es_MX": "Latin America", "es_US": "Latin America", "pt_BR": "Latin America",
            "en_US": "North America", "fr_CA": "North America",
            "en_GB": "Western Europe"
        }
        df["region"] = df["language_code"].map(lang_to_region).fillna("Other")

        # Identify TF Subcategory Column
        TF_COL = "tf_subcategory"
        if TF_COL not in df.columns:
            for c in df.columns:
                if "tf" in c.lower() and "sub" in c.lower(): 
                    TF_COL = c
                    break
        
        if TF_COL not in df.columns:
            print("Viz 09: 'tf_subcategory' column not found. Skipping.")
            return

        # Rename models for display
        df['model_display'] = df['model_name'].replace({
            'model_a': 'Base', 'model_b': 'Test',
            'Model A': 'Base', 'Model B': 'Test'
        })

        # Filter: Only Major Truthfulness Issues
        tf_failures = df[df["truthfulness"] == 1].copy()
        
        if tf_failures.empty:
            print("Viz 09: No major Truthfulness failures found.")
            return

        # Clean Subcats
        tf_failures[TF_COL] = tf_failures[TF_COL].fillna("Uncategorized").astype(str)
        
        # --- ADD OVERALL REGION ---
        # We duplicate the dataframe, label the region as 'Overall', and append it
        overall_df = tf_failures.copy()
        overall_df['region'] = 'Overall'
        combined_failures = pd.concat([tf_failures, overall_df], ignore_index=True)

        # ----------------------------
        # 2. Aggregation
        # ----------------------------
        # Group by Region, Model, Subcat
        grouped = combined_failures.groupby(['region', 'model_display', TF_COL]).size().reset_index(name='count')
        
        # Calculate Total failures per Region+Model to get %
        totals = grouped.groupby(['region', 'model_display'])['count'].transform('sum')
        grouped['percentage'] = (grouped['count'] / totals) * 100

        # Save Data
        os.makedirs(os.path.dirname(output_data_path), exist_ok=True)
        grouped.to_csv(output_data_path, index=False)
        print(f"✓ Saved data to: {output_data_path}")

        # ----------------------------
        # 3. Plotting (Faceted Stacked Bars)
        # ----------------------------
        # Ensure 'Overall' is first, then alphabetical
        unique_regions = sorted(grouped['region'].unique())
        if 'Overall' in unique_regions:
            unique_regions.remove('Overall')
            unique_regions.insert(0, 'Overall')
            
        models = ['Base', 'Test']
        subcats = sorted(grouped[TF_COL].unique())
        
        # Assign colors to subcategories
        colors = cm.get_cmap('tab20', len(subcats))
        color_map = {subcat: colors(i) for i, subcat in enumerate(subcats)}

        # Create Subplots
        n_regions = len(unique_regions)
        cols = min(n_regions, 3)
        rows = (n_regions + cols - 1) // cols
        
        # Increase figure height slightly to accommodate the legend being higher
        fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows + 1), sharey=True)
        axes = axes.flatten() if n_regions > 1 else [axes]

        for i, region in enumerate(unique_regions):
            ax = axes[i]
            region_data = grouped[grouped['region'] == region]
            
            bottoms = {m: 0 for m in models}
            
            # Plot stacked bars
            for subcat in subcats:
                vals = []
                for m in models:
                    row = region_data[(region_data['model_display'] == m) & (region_data[TF_COL] == subcat)]
                    vals.append(row['percentage'].values[0] if not row.empty else 0)
                
                ax.bar(models, vals, bottom=[bottoms[m] for m in models], 
                       label=subcat if i == 0 else "", color=color_map[subcat], alpha=0.9, width=0.6)
                
                for j, m in enumerate(models):
                    bottoms[m] += vals[j]

            # Add Count Labels at the top of the bars
            # We calculate the total count for each model in this region again
            for m_idx, m in enumerate(models):
                total_count = region_data[region_data['model_display'] == m]['count'].sum()
                if total_count > 0:
                    ax.text(m_idx, 102, f"n={total_count}", ha='center', va='bottom', fontsize=10, fontweight='bold', color='black')

            ax.set_title(region, fontsize=12, fontweight='bold')
            ax.set_ylim(0, 115) # Increased Y limit to make room for "n=" labels
            if i % cols == 0:
                ax.set_ylabel("% of TF Failures")
            ax.grid(axis='y', linestyle='--', alpha=0.3)

        # Hide empty subplots
        for j in range(i + 1, len(axes)):
            axes[j].axis('off')

        # Global Legend - Moved Up
        handles, labels = axes[0].get_legend_handles_labels()
        # bbox_to_anchor=(x, y): y > 1 moves it above the plot area
        fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.92), 
                   ncol=min(len(subcats), 4), title="Failure Subcategory", frameon=True)

        plt.tight_layout()
        # Adjust layout to make room for the legend at the top
        plt.subplots_adjust(top=0.90)
        
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        plt.savefig(output_image_path, bbox_inches='tight', dpi=300)
        print(f"✓ Saved image to: {output_image_path}")
        plt.close()

    except Exception as e:
        print(f"Error in viz_09: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()