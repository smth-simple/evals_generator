#!/usr/bin/env python3
"""
Visualization 0: Language + Overall Deltas + Pref + Mean Likert
Designed to run inside the ReportGeneratorV2 pipeline.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm, colors
from matplotlib.patches import Rectangle
import warnings

warnings.filterwarnings('ignore')

def main():
    # ----------------------------
    # 0. Integration Setup
    # ----------------------------
    # ReportGeneratorV2 provides these two variables:
    dataset_path = os.environ.get('DATASET_PATH') 
    output_dir = os.environ.get('OUTPUT_DIR')

    # Fallback for manual testing
    if not dataset_path:
        dataset_path = 'evals_data.csv' # Default if running manually
    if not output_dir:
        output_dir = 'viz_output'

    # Define strict output filenames so the report generator can find them
    output_image_path = os.path.join(output_dir, 'viz_00_summary.png')
    output_data_path = os.path.join(output_dir, 'viz_00_data.csv')

    print(f"Viz_00: Reading from {dataset_path}")
    print(f"Viz_00: Writing to {output_image_path}")

    try:
        # ----------------------------
        # 1. Load data
        # ----------------------------
        if not os.path.exists(dataset_path):
            print(f"Error: Dataset not found at {dataset_path}", file=sys.stderr)
            sys.exit(1)
            
        df = pd.read_csv(dataset_path)

        # ----------------------------
        # 2. Define major flags
        # ----------------------------
        df["IF_major"] = df["instruction_following"] == 1
        df["TF_major"] = df["truthfulness"] == 1
        df["LOC_major"] = df["loc"] == 1
        df["RL_major"] = df["response_length"].abs() == 2

        # ----------------------------
        # 3. Define base and test models
        # ----------------------------
        # Ensure we are looking for the raw names from the CSV (usually model_a / model_b)
        base_model = "model_a"
        test_model = "model_b"

        # ----------------------------
        # 4. Per-language, per-model major rates
        # ----------------------------
        agg = (
            df.groupby(["language_code", "model_name"])
            .agg(
                IF_major_rate=("IF_major", "mean"),
                TF_major_rate=("TF_major", "mean"),
                LOC_major_rate=("LOC_major", "mean"),
                RL_major_rate=("RL_major", "mean"),
            )
            .reset_index()
        )

        pivot = agg.pivot(index="language_code", columns="model_name")

        # ----------------------------
        # 5. Calculate Deltas
        # ----------------------------
        summary = pd.DataFrame(index=pivot.index)

        for metric in ["IF_major_rate", "TF_major_rate", "LOC_major_rate", "RL_major_rate"]:
            if (metric, test_model) in pivot.columns and (metric, base_model) in pivot.columns:
                summary[f"{metric}_delta_pp"] = (
                    (pivot[(metric, test_model)] - pivot[(metric, base_model)]) * 100.0
                )
            else:
                summary[f"{metric}_delta_pp"] = 0.0

        # ----------------------------
        # 6. Preference Logic
        # ----------------------------
        df_pref = df[~df["likert"].isna()].copy()

        def preference_net_row_based(series):
            n_rows = len(series)
            if n_rows == 0: return np.nan
            base_rows = ((series >= 1) & (series <= 3)).sum()
            test_rows = ((series >= 5) & (series <= 7)).sum()
            n_tasks = n_rows / 2.0
            if n_tasks == 0: return 0
            base_rate = (base_rows / 2.0) / n_tasks
            test_rate = (test_rows / 2.0) / n_tasks
            return (test_rate - base_rate) * 100.0

        pref_by_lang = df_pref.groupby("language_code")["likert"].apply(preference_net_row_based)
        summary["pref_net_test_minus_base_pp"] = summary.index.map(pref_by_lang)
        
        mean_likert_by_lang = df_pref.groupby("language_code")["likert"].mean()
        summary["mean_likert"] = summary.index.map(mean_likert_by_lang)

        # ----------------------------
        # 7. Add OVERALL row
        # ----------------------------
        overall_agg = (
            df.groupby("model_name")
            .agg(
                IF_major_rate=("IF_major", "mean"),
                TF_major_rate=("TF_major", "mean"),
                LOC_major_rate=("LOC_major", "mean"),
                RL_major_rate=("RL_major", "mean"),
            )
            .reset_index()
        )

        try:
            overall_base = overall_agg[overall_agg["model_name"] == base_model].iloc[0]
            overall_test = overall_agg[overall_agg["model_name"] == test_model].iloc[0]
            overall_IF_delta = (overall_test["IF_major_rate"] - overall_base["IF_major_rate"]) * 100.0
            overall_TF_delta = (overall_test["TF_major_rate"] - overall_base["TF_major_rate"]) * 100.0
            overall_LOC_delta = (overall_test["LOC_major_rate"] - overall_base["LOC_major_rate"]) * 100.0
            overall_RL_delta = (overall_test["RL_major_rate"] - overall_base["RL_major_rate"]) * 100.0
        except:
            overall_IF_delta = 0
            overall_TF_delta = 0
            overall_LOC_delta = 0
            overall_RL_delta = 0

        overall_pref_delta = preference_net_row_based(df_pref["likert"])
        overall_mean_likert = df_pref["likert"].mean()

        overall_row = pd.DataFrame([{
            "language": "Overall",
            "IF_major_rate_delta_pp": overall_IF_delta,
            "TF_major_rate_delta_pp": overall_TF_delta,
            "LOC_major_rate_delta_pp": overall_LOC_delta,
            "RL_major_rate_delta_pp": overall_RL_delta,
            "pref_net_test_minus_base_pp": overall_pref_delta,
            "mean_likert": overall_mean_likert,
        }])

        # ----------------------------
        # 8. Combine & Save Data
        # ----------------------------
        summary_lang = summary.reset_index().rename(columns={"language_code": "language"})
        summary_lang = summary_lang.sort_values(by=["pref_net_test_minus_base_pp", "language"], ascending=[False, True]).reset_index(drop=True)
        summary = pd.concat([overall_row, summary_lang], ignore_index=True)
        summary["mean_likert_centered"] = summary["mean_likert"] - 4.0

        os.makedirs(os.path.dirname(output_data_path), exist_ok=True)
        summary.to_csv(output_data_path, index=False)

        # ----------------------------
        # 9. Plotting (Table-Style Bar Chart)
        # ----------------------------
        metrics_to_plot = ["IF_major_rate_delta_pp", "TF_major_rate_delta_pp", "LOC_major_rate_delta_pp", "RL_major_rate_delta_pp", "pref_net_test_minus_base_pp", "mean_likert_centered"]
        metric_labels = ["Δ IF major (pp)", "Δ TF major (pp)", "Δ LOC major (pp)", "Δ RL major (pp)", "Δ Pref (test-base, pp)", "Mean likert (vs 4)"]
        languages = summary["language"].tolist()
        data = summary[metrics_to_plot].fillna(0).values

        n_rows, n_metrics = data.shape
        lmarena_bases = ["en", "zh", "fr", "de", "es", "ru", "ja", "ko"]
        is_lmarena_row = [False if str(l) == "Overall" else any(str(l).startswith(base) for base in lmarena_bases) for l in languages]

        vmax = np.nanmax(np.abs(data))
        if vmax == 0 or np.isnan(vmax): vmax = 1.0
        norm = colors.Normalize(vmin=-vmax, vmax=vmax)
        cmap = cm.get_cmap("coolwarm")

        fig, ax = plt.subplots(figsize=(14, 0.5 * n_rows + 2))
        ax.set_xlim(0, n_metrics)
        ax.set_ylim(0, n_rows)
        ax.set_xticks(np.arange(0, n_metrics + 1, 1))
        ax.set_yticks(np.arange(0, n_rows + 1, 1))
        ax.grid(which="both", axis="both")
        ax.set_xticks(np.arange(n_metrics) + 0.5, minor=False)
        ax.set_yticks(np.arange(n_rows) + 0.5, minor=False)
        ax.set_xticklabels(metric_labels, rotation=0, ha="center", color="black", fontsize=12)
        ax.set_yticklabels(languages, color="black", fontsize=12)
        ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)
        ax.invert_yaxis()
        for spine in ax.spines.values(): spine.set_visible(False)

        max_half_width = 0.4
        bar_height = 0.8

        # Draw LMArena background
        for i in range(n_rows):
            if is_lmarena_row[i]:
                ax.add_patch(Rectangle((0, i), n_metrics, 1.0, facecolor="#fff9b0", alpha=0.6, zorder=0))

        # Draw Bars & Text
        for i in range(n_rows):
            for j in range(n_metrics):
                val = data[i, j]
                cx, cy = j + 0.5, i + 0.5
                frac = min(abs(val) / vmax, 1.0)
                width = frac * max_half_width
                x_left = cx if val >= 0 else cx - width
                
                ax.add_patch(Rectangle((x_left, cy - bar_height/2), width, bar_height, facecolor=cmap(norm(val)), edgecolor="black", linewidth=0.5, zorder=1))
                
                text_val = summary.loc[i, "mean_likert"] if metrics_to_plot[j] == "mean_likert_centered" else val
                text_str = f"{text_val:.2f}" if metrics_to_plot[j] == "mean_likert_centered" else f"{text_val:.1f}"
                
                ax.text(cx, cy + bar_height * 0.35, text_str, ha="center", va="center", fontsize=12, fontweight="bold", color="black", bbox=dict(boxstyle="round,pad=0.15", facecolor="white", alpha=0.7, edgecolor="none"), zorder=2)

        ax.set_title("Overall + per-language net major error rates, preference, and mean likert", color="black", fontsize=14, fontweight="bold", pad=20)
        plt.tight_layout(rect=[0, 0, 1, 0.94])
        
        # Save
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        plt.savefig(output_image_path, bbox_inches='tight', dpi=300)
        print(f"Viz_00: Success! Saved to {output_image_path}")
        plt.close()

    except Exception as e:
        print(f"Viz_00 Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()