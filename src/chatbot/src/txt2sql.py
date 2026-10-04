from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import torch
import os
from src.chatbot.src.utils import load_model, load_tokenizer, inference_text

# =======================
# CONFIG
# =======================
BASE_MODEL_ID = "deepseek-ai/deepseek-coder-1.3b-instruct"
LORA_PATH = "/home/conthorcon/work/agent/AquaSupplyAI/src/chatbot/finetune/checkpoints/deepseek/txt2sql_fullv2_550"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

MAX_NEW_TOKENS = 512

# =======================
# INSTRUCTION
# =======================
with open("src/chatbot/prompts/prompt_txt2sqlv0", "r", encoding="utf-8") as f:
    INSTRUCTION = f.read()
INSTRUCTION = """
You are an AI assistant specialized in generating SQL queries.
"""

# MODEL = load_model(BASE_MODEL_ID, LORA_PATH)
# TOKENIZER = load_tokenizer(BASE_MODEL_ID, LORA_PATH)
MODEL = None
TOKENIZER = None

# =======================
# GENERATE
# =======================
def generate_sql(question, tokenizer=TOKENIZER, model=MODEL, max_new_tokens=MAX_NEW_TOKENS):
    messages = [
        {"role": "system", "content": INSTRUCTION},
        {"role": "user", "content": question}
    ]

    sql = inference_text(messages, tokenizer, model, max_new_tokens=max_new_tokens)
    return sql.strip()



# =======================
# MAIN TEST
# =======================
if __name__ == "__main__":
    tokenizer = load_tokenizer()
    model = load_model()

    question = "Tổng tiền bán hàng tại Tân Bình là bao nhiêu?"

    print("\n=== RESULT ===")
    print(generate_sql(question, tokenizer, model))
