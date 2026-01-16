# LLM Evals Report Generator

A forensic evaluation pipeline that compares two Large Language Models (Base vs. Test) using a multi-stage analysis process. It combines quantitative visualization with qualitative LLM-driven analysis to produce a professional, evidence-backed DOCX report.

## 📂 Directory Structure

Ensure your directory looks like this before running:

```text
evals_generator/
├── evals_data.csv                  # Input dataset (Must contain: model_name, language_code, likert, etc.)
├── report_generator_v2.py          # Main Orchestrator script
├── evals_report_config_v2.json     # Main path & settings config
├── models.json                     # Model selection (Context window, Temp, Provider)
├── configurable_prompts_v2.json    # Prompts for every stage of analysis
├── visualization_scripts/          # Directory containing Python viz scripts
│   ├── viz_00_language...py
│   ├── viz_16_composite_score...py
│   └── ... (other scripts)
├── viz_output/                     # Generated PNGs and CSVs appear here
└── report_output/                  # JSON states and Final DOCX appear here
```

# 🚀 Setup & Installation
1. Prerequisites
Python 3.8+

A valid API Key (OpenAI, Anthropic, or LiteLLM Proxy)

2. Install Dependencies
Create a virtual environment and install the required packages:

Bash

python3 -m venv venv
source venv/bin/activate
pip install pandas matplotlib seaborn python-docx litellm
3. Environment Variables
You must set your API key before running the script.

Option A: Using OpenAI Directly

Bash

export OPENAI_API_KEY="sk-..."
Option B: Using Anthropic Directly

Bash

export ANTHROPIC_API_KEY="sk-ant-..."
Option C: Using LiteLLM Proxy (Recommended for custom models) If you are pointing to a local proxy or custom endpoint:

Bash

export OPENAI_API_BASE="[http://0.0.0.0:4000](http://0.0.0.0:4000)"  # Your Proxy URL
export OPENAI_API_KEY="sk-litellm-..."        # Your Proxy Key
⚙️ Configuration
1. Model Selection (models.json)
Control which LLM performs which step. You can use different models for heavy reasoning vs. basic checks.

Prefix Guide:

For OpenAI: "gpt-4o"

For Anthropic: "anthropic/claude-3-opus-..."

For LiteLLM Proxy: "openai/your-custom-model-name"

2. Prompt Engineering (configurable_prompts_v2.json)
Identifying: Controls how the model finds failure patterns.

Synthesis: Controls the "Root Cause Analysis" logic.

Report Sections: Controls the final writing tone and structure of the DOCX.

🏃 How to Run
You can run the full pipeline at once or step-by-step for debugging.

Full Auto Mode
Generates visualizations, analyzes data, synthesizes insights, and writes the Word doc in one go.

Bash

python3 report_generator_v2.py --step all
Step-by-Step (Recommended for tuning)
Step 1: Visualization Runs the scripts in visualization_scripts/ to generate PNG charts and CSV data tables in viz_output/.

Bash

python3 report_generator_v2.py --step viz
Step 2: Identifying The LLM scans the raw data to find "Major Failures," "Regional Patterns," and "Hard Prompt" issues. Saves state_identifying.json.

Bash

python3 report_generator_v2.py --step identifying
Step 3: Synthesis The "Forensic Step." Connects the qualitative findings (Step 2) with the quantitative charts (Step 1). Produces the synthesis_output.md brief.

Bash

python3 report_generator_v2.py --step synthesis
Step 4: Rollout Writes the final report sections based on the Synthesis brief. Inserts figures and tables dynamically. Saves state_rollout.json.

Bash

python3 report_generator_v2.py --step rollout
Step 5: Check & Compile Validates the text and assembles the final .docx.

Bash

python3 report_generator_v2.py --step check
📊 Troubleshooting
1. "Image Not Found" in Word Doc

Check the viz_output/ folder. Do the PNGs exist?

If not, run python3 report_generator_v2.py --step viz.

Ensure the filename in FIGURE_CAPTIONS (inside report_generator_v2.py) matches the actual filename.

2. LLM Authentication Errors

Double-check your OPENAI_API_KEY or ANTHROPIC_API_KEY.

If using a specific model name in models.json (e.g., claude-opus), ensure your provider or proxy actually supports that exact name.

3. "Context Window Exceeded"

If your dataset is huge, the context payload might be too large.

Edit report_generator_v2.py to lower the truncation limit (currently set to 300,000 characters in _call_llm).
