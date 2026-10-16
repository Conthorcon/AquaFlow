"""Lazy-loaded text-to-SQL model, used only by the AI server."""
import os
from pathlib import Path
from threading import Lock
from src.chatbot.src.utils import load_model, load_tokenizer, inference_text

ROOT = Path(__file__).resolve().parents[3]
BASE_MODEL_ID = os.environ.get("AI_BASE_MODEL", "deepseek-ai/deepseek-coder-1.3b-instruct")
LORA_PATH = os.environ.get("AI_LORA_PATH", str(ROOT / "src/chatbot/finetune/checkpoints/deepseek/txt2sql_fullv2_550"))
INSTRUCTION = (ROOT / "src/chatbot/prompts/prompt_txt2sqlv0").read_text(encoding="utf-8")
MAX_NEW_TOKENS = 512
MODEL = None
TOKENIZER = None
_model_lock = Lock()


def generate_sql(question, tokenizer=None, model=None, max_new_tokens=MAX_NEW_TOKENS):
    global MODEL, TOKENIZER
    if tokenizer is None or model is None:
        with _model_lock:
            if MODEL is None or TOKENIZER is None:
                loaded_tokenizer = load_tokenizer(BASE_MODEL_ID, LORA_PATH)
                loaded_model = load_model(BASE_MODEL_ID, LORA_PATH)
                TOKENIZER, MODEL = loaded_tokenizer, loaded_model
        tokenizer, model = TOKENIZER, MODEL
    messages = [
        {"role": "system", "content": INSTRUCTION},
        {"role": "user", "content": question},
    ]
    return inference_text(messages, tokenizer, model, max_new_tokens=max_new_tokens).strip()
