import os
import gc
import json
import time
import random
import numpy as np
import torch

from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training
)
from trl import SFTTrainer, SFTConfig
from huggingface_hub import login

# =============================
# 1. CONFIG
# =============================
ROOT_DIR = "/kaggle/working/"
MODEL_ID = "deepseek-ai/deepseek-coder-1.3b-instruct"
DATA_PATH = "/kaggle/input/datasets/khanhtruong3150/sql2txt-fullv2/sql2txt_fullv2.jsonl"

OUTPUT_DIR = os.path.join(ROOT_DIR, "out_trl_clean")
CACHE_DIR = os.path.join(ROOT_DIR, "cache")

os.makedirs(OUTPUT_DIR, exist_ok=True)

HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
SEED = 42
MAX_SEQ_LENGTH = 1024

# LoRA
LORA_R = 16
LORA_ALPHA = 16
LORA_DROPOUT = 0.05

# Training
TRAIN_ARGS = {
    "num_train_epochs": 3,
    "per_device_train_batch_size": 4,
    "per_device_eval_batch_size": 4,
    "gradient_accumulation_steps": 8,
    "learning_rate": 5e-5,
    "warmup_ratio": 0.05,
    "lr_scheduler_type": "cosine",
    "logging_steps": 10,
    "logging_first_step": True,
    "eval_strategy": "steps",
    "eval_steps": 50,
    "save_strategy": "steps",
    "save_steps": 100,
    "save_total_limit": 2,
    "load_best_model_at_end": True,
    "gradient_checkpointing": True,
    "max_grad_norm": 1.0,
    "report_to": "none",
    "seed": SEED,
}

USE_BF16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
DTYPE = torch.bfloat16 if USE_BF16 else torch.float16

# =============================
# 2. UTILS
# =============================
def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def clear_memory():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def get_param_stats(model):
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable


def find_all_linear_names(model):
    linear_cls = torch.nn.Linear
    names = set()
    for name, module in model.named_modules():
        if isinstance(module, linear_cls):
            names.add(name.split('.')[-1])
    return list(names)

# =============================
# 3. TOKENIZER
# =============================
print("Loading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_ID,
    cache_dir=CACHE_DIR,
    trust_remote_code=True,
    token=HF_TOKEN,
)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

tokenizer.padding_side = "right"

# =============================
# 4. DATASET
# =============================
print("Loading dataset...")

raw = load_dataset("json", data_files=DATA_PATH)["train"]
split = raw.train_test_split(test_size=0.1, seed=SEED)

train_raw = split["train"].shuffle(seed=SEED)
eval_raw = split["test"]

INSTRUCTION = """
You are an AI assistant specialized in generating SQL queries. Your task is to convert user questions into accurate SQL query based on the database schema provided below.

### Database Schema:
employee (id, name, role): Employee information.
customer_group (id, name): Customer groups (e.g., distributor, retail customer).
product (id, name, cap_type, bottle_type, capacity): Product information.
purchase (id, description, total_amount, category, date): List of purchase batches (input costs).
product_price_config (id, product_id, group_id, price): Product pricing configuration for each customer group.
customer (id, name, phone, address, group_id): Customer information.
sale (id, delivery_employee_id, customer_id, total_amount, date_created, date_delivery, date_completed, tax, note, status): Sales order information.
sale_item (id, sale_id, product_id, quantity, price_at_sale): Details of items in each sales order.
inventory (id, product_id, quantity, note, last_updated): Actual inventory quantity of products.
purchase_category (id, name): Purchase categories.

### Important Rules:
- Only generate SQLite query by table and collumn of database schema provided above.
- Do NOT include explanations, comments, or any extra text.
- Return ONLY SQL query.
"""

def format_example(example):
    messages = [
        {"role": "system", "content": INSTRUCTION},
        {"role": "user", "content": example["input"]["question"]},
        {"role": "assistant", "content": example["input"]["query"]},
    ]

    full_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    prompt_text = tokenizer.apply_chat_template(messages[:-1], tokenize=False, add_generation_prompt=True)

    full_tokens = tokenizer(full_text, truncation=True, max_length=MAX_SEQ_LENGTH)
    prompt_tokens = tokenizer(prompt_text, truncation=True, max_length=MAX_SEQ_LENGTH)

    input_ids = full_tokens["input_ids"]
    labels = input_ids.copy()

    prompt_ids = prompt_tokens["input_ids"]
    full_ids = full_tokens["input_ids"]
    
    prompt_len = len(prompt_ids)
    
    if full_ids[:prompt_len] != prompt_ids:
        prompt_len = 0  # fallback tránh mask sai
    labels[:prompt_len] = [-100] * prompt_len

    return {
        "input_ids": input_ids,
        "attention_mask": full_tokens["attention_mask"],
        "labels": labels,
    }

print("Tokenizing dataset...")

train_ds = train_raw.map(format_example, remove_columns=train_raw.column_names)
eval_ds = eval_raw.map(format_example, remove_columns=eval_raw.column_names)

# =============================
# 5. MODEL
# =============================
def load_model(qlora=False):
    if qlora:
        bnb_cfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=DTYPE,
            bnb_4bit_use_double_quant=True,
        )

        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            quantization_config=bnb_cfg,
            device_map="auto",
            cache_dir=CACHE_DIR,
            trust_remote_code=True,
            token=HF_TOKEN,
        )

        model = prepare_model_for_kbit_training(model)

    else:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=DTYPE,
            device_map="auto",
            cache_dir=CACHE_DIR,
            trust_remote_code=True,
            token=HF_TOKEN,
        )

        model.gradient_checkpointing_enable()

    model.config.use_cache = False
    model.config.pad_token_id = tokenizer.pad_token_id

    return model

# =============================
# 6. TRAIN
# =============================
def train(qlora=False):
    clear_memory()
    set_seed(SEED)

    print("Loading model...")
    model = load_model(qlora)

    target_modules = find_all_linear_names(model)

    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=target_modules,
    )

    model = get_peft_model(model, lora_config)

    total, trainable = get_param_stats(model)
    print(f"Trainable: {trainable:,} / {total:,}")

    TRAIN_ARGS["bf16"] = USE_BF16
    TRAIN_ARGS["fp16"] = not USE_BF16
    TRAIN_ARGS["optim"] = "paged_adamw_8bit" if qlora else "adamw_torch"

    args = SFTConfig(
        output_dir=OUTPUT_DIR,
        max_length=MAX_SEQ_LENGTH,
        dataset_text_field=None,
        **TRAIN_ARGS
    )

    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
    )

    print("Training...")
    start = time.time()
    trainer.train()
    print(f"Done in {time.time() - start:.1f}s")

    # Save
    save_dir = os.path.join(OUTPUT_DIR, "adapter")
    model.save_pretrained(save_dir)
    tokenizer.save_pretrained(save_dir)

    with open(os.path.join(OUTPUT_DIR, "log.json"), "w") as f:
        json.dump(trainer.state.log_history, f, indent=2)

    clear_memory()

train(qlora=False)