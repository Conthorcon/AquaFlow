from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from peft import PeftModel
import sqlite3
import torch
from src.chatbot.src.utils import load_tokenizer, load_model, inference_text

# =======================
# CONFIG
# =======================
DB_PATH = "instance/aquasupply.db"

BASE_MODEL_ID = "meta-llama/Llama-3.2-1B-Instruct"
LORA_PATH = "/home/conthorcon/work/agent/AquaSupplyAI/src/chatbot/finetune/checkpoints/llama/sql2txt_fullv1"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MAX_NEW_TOKENS = 256

# =======================
# LOAD MODEL + TOKENIZER
# =======================
# TOKENIZER = load_tokenizer(BASE_MODEL_ID, LORA_PATH)
# MODEL = load_model(BASE_MODEL_ID, LORA_PATH)
TOKENIZER = None
MODEL = None

# =======================
# QUERY DATABASE
# =======================
def query_data(sql_sentence):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()
        cursor.execute(sql_sentence)

        rows = cursor.fetchall()

        result = [dict(row) for row in rows]

        return result

    finally:
        conn.close()

# =======================
# PROMPT
# =======================

INSTRUCTION = """
Bạn là một trợ lý phân tích dữ liệu bán hàng. Hãy dựa vào câu hỏi và kết quả truy vấn để trả lời người dùng một cách tự nhiên và chính xác.
"""

# =======================
# GENERATE NATURAL LANGUAGE
# =======================
def generate_nl(
    question,
    sql_sentence,
    result,
    model=MODEL,
    tokenizer=TOKENIZER,
    max_new_tokens=MAX_NEW_TOKENS
):
    try:
        data = query_data(sql_sentence)

        if not data:
            return "Không tìm thấy dữ liệu phù hợp."

    except Exception as e:
        print(f"SQL Error: {e}")
        return "OUT_OF_SCOPE"

    messages = [
        {"role": "system", "content": INSTRUCTION},
        {"role": "user", "content": f"Câu hỏi: {question}\nSQL: {sql_sentence}\nKết quả: {result}"},
    ]

    return inference_text(messages, tokenizer, model, device=DEVICE, max_new_tokens=max_new_tokens)


# =======================
# ORDER PRODUCT
# =======================
def get_prompt_order_product(message):
    return f"""
Bạn là trợ lý đặt hàng của AquaSupply.

Tin nhắn khách hàng:
{message}

Hãy phản hồi lịch sự và hỗ trợ khách hàng đặt hàng.
""".strip()


def order_product(message):
    prompt = get_prompt_order_product(message)

    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    outputs = PIPE(
        messages,
        max_new_tokens=256,
        do_sample=False,
        # temperature=0.0,
        return_full_text=False,
    )

    return outputs[0]["generated_text"][-1]["content"].strip()


# =======================
# MAIN
# =======================
if __name__ == "__main__":
    question = "What are the products?"
    sql = "SELECT * FROM product LIMIT 5"
    result = {
        "product_name": "nước suối",
        "quantity": 10,
        "price": 5000,
    }

    response = generate_nl(
        question=question,
        sql_sentence=sql,
        result=result,

    )

    print(response)