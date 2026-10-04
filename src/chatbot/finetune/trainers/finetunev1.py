import os
import gc
import torch
from copy import deepcopy
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments
)
from trl import SFTConfig, SFTTrainer

# --- 1. Cấu hình Hệ thống & Token ---
# Ưu tiên lấy từ biến môi trường, nếu không có mới xét đến biến input
root_dir = "/kaggle/working/"
HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
# MODEL_ID = "meta-llama/Llama-3.2-1B-Instruct"
MODEL_ID = "deepseek-ai/deepseek-coder-1.3b-instruct"
CACHE_DIR = os.path.join(root_dir,"cache")
OUTPUT_ROOT = os.path.join(root_dir,"out_full_trl")
os.makedirs(OUTPUT_ROOT, exist_ok=True)

# --- 2. Tham số Huấn luyện ---
MAX_SEQ_LENGTH = 256
SEED = 42

# Cấu hình LoRA
LORA_R = 16
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj"]

# Thiết lập Kiểu dữ liệu (Dtype)
USE_BF16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
DTYPE = torch.bfloat16 if USE_BF16 else torch.float16

# --- 3. Cấu hình Trainer (Common Kwargs) ---
COMMON_TRAIN_KWARGS = {
    "num_train_epochs": 3,  # tăng nhẹ vì dataset nhỏ
    # ❌ bỏ max_steps

    "per_device_train_batch_size": 4,
    "per_device_eval_batch_size": 4,
    "gradient_accumulation_steps": 8,  # effective batch = 32

    "learning_rate": 1e-4,  # ổn định hơn 2e-4
    "warmup_ratio": 0.05,   # tốt hơn warmup_steps cố định

    "lr_scheduler_type": "cosine",  # smooth hơn linear

    "logging_steps": 10,

    "eval_strategy": "steps",
    "eval_steps": 50,

    "save_strategy": "steps",
    "save_steps": 100,
    "save_total_limit": 2,  # tránh đầy disk
    "load_best_model_at_end": True,

    "bf16": USE_BF16,
    "fp16": not USE_BF16,

    "gradient_checkpointing": True,
    "optim": "adamw_torch",

    "report_to": "none",
    "seed": SEED,
}
# --- 4. Khởi tạo lưu trữ kết quả ---
histories = {}
run_stats = {}
infer_results = {}

# --- 5. Hàm dọn dẹp bộ nhớ (Tùy chọn nhưng nên có) ---
def flush_memory():
    gc.collect()
    torch.cuda.empty_cache()

print(f"Sẵn sàng huấn luyện với thiết bị: {'BF16' if USE_BF16 else 'FP16'}")

from datasets import load_dataset

# Load dataset từ file JSONL
raw_full = load_dataset(
    "json",
    data_files="/kaggle/input/datasets/khanhtruong3150/sql2txt-fullv2/sql2txt_fullv2.jsonl"
)

# Chia train / test
raw_split = raw_full["train"].train_test_split(test_size=0.1, seed=42)

train_raw = raw_split["train"]
eval_raw = raw_split["test"]

print(train_raw)
print(eval_raw)

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


def row_to_messages(example):
    return {
        "messages": [
            {"role": "system", "content": INSTRUCTION},
            {"role": "user", "content": example["input"]["question"]},
            {"role": "assistant", "content": example["input"]["query"]},
        ]
    }

# 3. Áp dụng chuyển đổi và xóa các cột cũ
# Sử dụng trực tiếp raw["train"] và raw["test"]
train_ds = train_raw.map(
    row_to_messages,
    remove_columns=train_raw.column_names
)

eval_ds = eval_raw.map(
    row_to_messages,
    remove_columns=eval_raw.column_names
)

# 4. Cấu hình Subsample (Lấy mẫu nhỏ để train nhanh hơn)
TRAIN_SUBSAMPLE = 4000
EVAL_SUBSAMPLE = 800
SEED = 42 # Đảm bảo SEED đã được định nghĩa từ phần code trước

if TRAIN_SUBSAMPLE and TRAIN_SUBSAMPLE < len(train_ds):
    train_ds = train_ds.shuffle(seed=SEED).select(range(TRAIN_SUBSAMPLE))

if EVAL_SUBSAMPLE and EVAL_SUBSAMPLE < len(eval_ds):
    eval_ds = eval_ds.shuffle(seed=SEED).select(range(EVAL_SUBSAMPLE))

# 5. Tạo tập mẫu để test nhanh (Inference Samples)
# Lấy nội dung câu hỏi từ vai trò "user" (index 1 trong list messages)
INFER_SAMPLES = [
    {"question": eval_ds[i]["messages"][1]["content"]}
    for i in range(min(3, len(eval_ds)))
]

# 6. Kiểm tra kết quả
print(f"Train size: {len(train_ds)} | Eval size: {len(eval_ds)}")
print("Sample input:", INFER_SAMPLES[0])

import os
import gc
import json
import torch

def clear_gpu():
    """Giải phóng bộ nhớ GPU và dọn rác hệ thống."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def apply_chat(example, tokenizer):
    """
    Convert messages -> single formatted string cho SFTTrainer.
    """
    msgs = example["messages"]

    # Validate cơ bản
    if not isinstance(msgs, list) or len(msgs) == 0:
        raise ValueError("Invalid messages format")

    # Trường hợp chuẩn: 1 hội thoại (list các dict)
    if isinstance(msgs[0], dict):
        return tokenizer.apply_chat_template(
            msgs,
            tokenize=False,
            add_generation_prompt=False
        )

    # Fallback: nếu msgs là list nhiều hội thoại (hiếm khi dùng)
    return "\n".join(
        tokenizer.apply_chat_template(
            m,
            tokenize=False,
            add_generation_prompt=False
        )
        for m in msgs
    )

def get_param_stats(model):
    """Tính toán số lượng tham số tổng và số lượng tham số có thể huấn luyện."""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)

    return {
        "total": total,
        "trainable": trainable,
        "ratio_pct": 100 * trainable / total if total > 0 else 0
    }

def save_run_results(output_dir, label, framework, mode, seconds, stats):
    """Lưu thông tin về hiệu suất huấn luyện vào file JSON."""
    os.makedirs(output_dir, exist_ok=True)

    stat_entry = {
        "run": label,
        "framework": framework,
        "mode": mode,
        "train_seconds": seconds,
        **stats, # Giải nén các chỉ số từ get_param_stats hoặc các stats khác
    }

    # Lưu vào biến global run_stats (giả định đã khai báo trước đó)
    run_stats[label] = stat_entry

    file_path = os.path.join(output_dir, "run_stats.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(stat_entry, f, indent=2, ensure_ascii=False)

def extract_assistant_answer(full_text):
    """Tách câu trả lời của trợ lý ra khỏi văn bản đầy đủ."""
    lower_text = full_text.lower()
    marker = "assistant"

    idx = lower_text.rfind(marker)
    if idx != -1:
        # Lấy phần văn bản sau chữ "assistant", loại bỏ dấu hai chấm, xuống dòng và khoảng trắng
        return full_text[idx + len(marker):].strip().lstrip(":\n ")

    return full_text.strip()


import time
import json
import os
from copy import deepcopy
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTConfig, SFTTrainer

def train_trl(qlora: bool, output_dir: str, label: str, target_modules: list):
    clear_gpu()
    print(f"\n=== {label} ===")

    # 1. Khởi tạo Tokenizer
    tok = AutoTokenizer.from_pretrained(
        MODEL_ID,
        cache_dir=CACHE_DIR,
        trust_remote_code=True,
        token=HF_TOKEN,
    )
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "right"

    # 2. Khởi tạo Model (Hỗ trợ QLoRA hoặc LoRA tiêu chuẩn)
    if qlora:
        # Cấu hình 4-bit quantization
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
        # Chuẩn bị model để train k-bit (đặc thù cho QLoRA)
        model = prepare_model_for_kbit_training(
            model,
            use_gradient_checkpointing=True,
            gradient_checkpointing_kwargs={"use_reentrant": False},
        )
    else:
        # LoRA tiêu chuẩn (không quantize, load ở FP16/BF16)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=DTYPE,
            device_map="auto",
            cache_dir=CACHE_DIR,
            trust_remote_code=True,
            token=HF_TOKEN,
        )

    model.config.use_cache = False

    # 3. Cấu hình LoRA Adapter
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=target_modules,
    )
    model = get_peft_model(model, lora_config)

    # Thống kê tham số
    ps = get_param_stats(model)
    print(f"Trainable params: {ps['trainable']:,} ({ps['ratio_pct']:.3f}%)")

    # 4. Thiết lập tham số huấn luyện
    kw = dict(COMMON_TRAIN_KWARGS)
    # Sử dụng optimizer paged nếu dùng QLoRA để tiết kiệm VRAM
    kw["optim"] = "paged_adamw_8bit" if qlora else "adamw_torch"

    args = SFTConfig(
        output_dir=output_dir,
        max_length=MAX_SEQ_LENGTH,
        dataset_text_field=None, # Sử dụng formatting_func thay thế
        **kw
    )

    # 5. Khởi tạo Trainer
    trainer = SFTTrainer(
        model=model,
        processing_class=tok,
        args=args,
        train_dataset=train_ds,
        # max_seq_length=MAX_SEQ_LENGTH,
        eval_dataset=eval_ds,
        formatting_func=lambda ex: apply_chat(ex, tok),
    )

    # 6. Bắt đầu huấn luyện
    t0 = time.perf_counter()
    trainer.train()
    elapsed = time.perf_counter() - t0
    print(f"[Done] Training took: {elapsed:.1f}s")

    # 7. Lưu kết quả và Adapter
    adapter_dir = os.path.join(output_dir, "adapter")
    model.save_pretrained(adapter_dir)
    tok.save_pretrained(adapter_dir)

    # Lưu log history
    log = deepcopy(trainer.state.log_history)
    with open(os.path.join(output_dir, "log_history.json"), "w") as f:
        json.dump(log, f, indent=2)

    histories[label] = log

    # Lưu thông số chạy (Sử dụng hàm đã viết ở bước trước)
    save_run_results(
        output_dir=output_dir,
        label=label,
        framework="trl",
        mode="qlora" if qlora else "lora",
        seconds=elapsed,
        stats=ps
    )

    # 8. Giải phóng bộ nhớ
    del trainer, model
    clear_gpu()

train_trl(
        qlora=False,
        output_dir=os.path.join(OUTPUT_ROOT, "trl_lora_" + str(i)),
        label="TRL + LoRA",
        target_modules=TARGET_MODULES
    )