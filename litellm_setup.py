# Put this in a file called litellm_setup.py in the bloom directory
import os
import litellm

# Configure for Scale's LiteLLM
os.environ["OPENAI_API_BASE"] = "https://litellm.ml-serving-internal.scale.com/v1"
os.environ["OPENAI_API_KEY"] = "sk-NsR7JAKkTxpElKDtU3LO6Q"

# Tell LiteLLM to use OpenAI format
litellm.drop_params = True  # Important for Scale compatibility
litellm.add_function_to_prompt = False