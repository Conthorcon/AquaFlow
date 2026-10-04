import time
import json
import re
import argparse
from datetime import datetime

from src.chatbot.src.txt2sql import generate_sql
from src.chatbot.src.sql2txt import query_data, generate_nl
from src.chatbot.src.utils import load_model, load_tokenizer

from src.database.models import Customer, Product
from app import app

import pandas as pd
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import random
from rapidfuzz import process, fuzz
from unidecode import unidecode
import tqdm

# =========================================================
# CONFIG
# =========================================================
DATA_TEST_PATH = "/home/conthorcon/work/agent/AquaSupplyAI/src/chatbot/finetune/datasets/test/test_chatbot_query.jsonl"

LORA_T2S_PATH = "/home/conthorcon/work/agent/AquaSupplyAI/src/chatbot/finetune/checkpoints/deepseek/t2s_fullv2_e10_siminst_v0"
MODEL_T2S_ID = "deepseek-ai/deepseek-coder-1.3b-instruct"

LORA_S2T_PATH = "/home/conthorcon/work/agent/AquaSupplyAI/src/chatbot/finetune/checkpoints/llama/s2t_fullv2_e3"
MODEL_S2T_ID = "meta-llama/Llama-3.2-1B-Instruct"

MAX_NEW_TOKENS_T2S = 256
MAX_NEW_TOKENS_S2T = 256

MODEL_T2S = load_model(MODEL_T2S_ID, LORA_T2S_PATH)
TOKENIZER_T2S = load_tokenizer(MODEL_T2S_ID, LORA_T2S_PATH)

MODEL_S2T = load_model(MODEL_S2T_ID, LORA_S2T_PATH)
TOKENIZER_S2T = load_tokenizer(MODEL_S2T_ID, LORA_S2T_PATH)

SIM_THRESHOLD = 0.5

original_print = print

PRINT_ENABLED = True

if not PRINT_ENABLED:
    print = lambda *args, **kwargs: None

# ===== LOAD MODEL EMBEDDING =====
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# ===== HELPER =====
def get_choices(sql):
    final_sql_pos = sql.find("SELECT")
    

def fuzzy_match(bad_sql, choices):
    print(bad_sql)

    start_index = bad_sql.upper().rfind("SELECT")
    final_sql = bad_sql[start_index:].rstrip(')')

    match = re.search(r"p\.name\s*=\s*'(.*?)'", final_sql)
    if not match:
        match = re.search(r"name\s*=\s*'(.*?)'", final_sql)

    if not match:
        return bad_sql

    start_index = final_sql.upper().rfind("FROM")
    end_index = final_sql.upper().rfind("WHERE")
    table = final_sql[start_index:end_index].strip()

    if 'customer' in table:
        choices = Customer.query.all()
        choices = [c.name for c in choices]
    elif 'product' in table:
        choices = Product.query.all()
        choices = [p.name for p in choices]
    else: 
        return bad_sql

    wrong_name = match.group(1)
    
    best_match = None
    highest_score = 0
    
    for choice in choices:
        score = fuzz.token_set_ratio(wrong_name, choice)
        
        if score > highest_score:
            highest_score = score
            best_match = choice

    if highest_score > 70:
        return bad_sql.replace(f"'{wrong_name}'", f"'{best_match}'")
    
    return bad_sql

def normalize_sql(sql):
    return " ".join(sql.lower().strip().split())

def exact_match(pred, gt):
    return int(normalize_sql(pred) == normalize_sql(gt))

def execute_sql(conn, sql):
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows, True
    except Exception as e:
        return None, False

def compare_result(res1, res2):
    return int(str(res1) == str(res2))

def semantic_similarity(s1, s2):
    emb1 = embed_model.encode(s1)
    emb2 = embed_model.encode(s2)
    return cosine_similarity([emb1], [emb2])[0][0]

# =========================================================
# UTILS
# =========================================================
def normalize_sql(sql: str):
    return re.sub(r"\s+", " ", sql.strip().lower())


def safe_execute(sql):
    try:
        if not sql.startswith("SELECT"):
            if sql.strip() == "" or sql.strip() == "OUT_OF_SCOPE":
                return "OUT_OF_SCOPE", None
            return None, "Invalid SQL query"

        return query_data(sql), None

    except Exception as e:
        return None, str(e)


def compare_sql(pred_sql, expected_sql):
    """
    Execution-based evaluation
    """
    pred_res, err1 = safe_execute(pred_sql)
    exp_res, err2 = safe_execute(expected_sql)

    if err1 or err2:
        return False, f"Execution error: pred={err1}, expected={err2}"
    def normalize_result(res):
        normalized = []

        for row in res:
            values = tuple(row.values())
            normalized.append(values)

        return normalized

    return normalize_result(pred_res) == normalize_result(exp_res), None


def compare_answer(pred, expected):
    metrics = semantic_similarity(pred, expected)

    print(metrics)
    if metrics > SIM_THRESHOLD:
        return 1, metrics
    return 0, metrics


# =========================================================
# MAIN TEST
# =========================================================

def run_test(
    file_path,
    mode="both",  # txt2sql | sql2txt | both
    save_log=True,
    retry=1
):
    stats = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "sql_correct": 0,
        "answer_correct": 0,
    }

    time_stats = {
        "t2sql": 0,
        "sql_exec": 0,
        "sql2text": 0,
    }

    pred_cases = []

    failed_cases = []
    failed_indices = []
    logs = []
    metric_counts = {
        "above_0_5": 0,
        "above_0_8": 0,
    }

    with open(file_path, "r", encoding="utf-8") as f:
        test_cases = [json.loads(line) for line in f if line.strip()]

    for idx, tc in enumerate(tqdm.tqdm(test_cases[17:20])):
        question = tc["question"].strip()
        expected_sql = tc["query"]
        expected_answer = tc["answer"]

        pred_log = {
            "question": question,
            "query": None,
            "result": None,
            "answer": None,
        }

        stats["total"] += 1

        print("=" * 60)
        print(f"[{idx+1}] {question}")

        log = {
            "question": question,
            "pred_sql": None,
            "sql_result": None,
            "answer": None,
            "exp_answer": None,
            "sql_correct": False,
            "answer_correct": False,
            "error": None,
            "time": {},
        }

        # =====================================================
        # TEXT2SQL
        # =====================================================
        if mode in ["txt2sql", "both"]:
            success = False

            for attempt in range(retry + 1):
                try:
                    start = time.time()

                    pred_sql = generate_sql(question, tokenizer=TOKENIZER_T2S, model=MODEL_T2S, max_new_tokens=MAX_NEW_TOKENS_T2S)
                    pred_sql = fuzzy_match(pred_sql, None)

                    t = time.time() - start
                    time_stats["t2sql"] += t

                    log["pred_sql"] = pred_sql
                    log["time"]["t2sql"] = t
                    pred_log["query"] = pred_sql

                    success = True
                    break

                except Exception as e:
                    if attempt == retry:
                        log["error"] = f"Text2SQL: {e}"
                        failed_cases.append(log)
                        stats["failed"] += 1

                        print(f"❌ Text2SQL Error: {e}")

            if not success:
                continue

        else:
            # sql2txt mode dùng GT SQL
            log["pred_sql"] = expected_sql

        print(f"SQL: {pred_sql}")
        print(f"Expected SQL: {expected_sql}")

        # =====================================================
        # SQL EXEC
        # =====================================================
        start = time.time()

        sql_result, err = safe_execute(pred_sql)

        t = time.time() - start
        time_stats["sql_exec"] += t

        log["time"]["sql_exec"] = t

        if err:
            log["error"] = f"SQL Execution: {err}"
            failed_cases.append(log)
            stats["failed"] += 1

            print(f"❌ SQL Error: {err}")
            continue

        log["sql_result"] = str(sql_result)
        pred_log["result"] = str(sql_result)

        print(f"Result: {sql_result}")

        # =====================================================
        # SQL EVAL
        # =====================================================
        if mode in ["txt2sql", "both"]:
            sql_ok, sql_err = compare_sql(pred_sql, expected_sql)

            log["sql_correct"] = sql_ok

            if sql_ok:
                stats["sql_correct"] += 1

        else:
            sql_ok = True

        # =====================================================
        # SQL2TEXT
        # =====================================================
        if mode in ["sql2txt", "both"]:
            try:
                start = time.time()

                answer = generate_nl(
                    question,
                    pred_sql,
                    sql_result,
                    tokenizer=TOKENIZER_S2T,
                    model=MODEL_S2T,
                    max_new_tokens=MAX_NEW_TOKENS_S2T
                )

                t = time.time() - start
                time_stats["sql2text"] += t

                log["answer"] = answer
                log["exp_answer"] = expected_answer
                log["time"]["sql2text"] = t
                pred_log["answer"] = answer

                print(f"Answer: {answer}")
                print(f"Expected Answer: {expected_answer}")

            except Exception as e:
                log["error"] = f"SQL2Text: {e}"
            
                failed_cases.append(log)
                stats["failed"] += 1

                print(f"❌ SQL2Text Error: {e}")
                continue

            # =================================================
            # ANSWER EVAL
            # =================================================
            ans_ok, metrics = compare_answer(
                answer,
                expected_answer
            )

            log["answer_correct"] = ans_ok

            if ans_ok:
                stats["answer_correct"] += 1

                if metrics > 0.8:
                    metric_counts["above_0_8"] += 1
                else:
                    metric_counts["above_0_5"] += 1

        else:
            ans_ok = True

        # =====================================================
        # FINAL PASS
        # =====================================================
        if sql_ok and ans_ok:
            stats["passed"] += 1
            print("✅ PASS")
        else:
            stats["failed"] += 1
            failed_cases.append(log)
            failed_indices.append(idx)
            
            print("❌ FAIL")

        pred_cases.append(pred_log)
        logs.append(log)

    # =========================================================
    # SUMMARY
    # =========================================================
    original_print("\n" + "=" * 60)
    original_print(f"📊 SUMMARY ({mode})")
    original_print(json.dumps(stats, indent=2))

    if stats["total"] > 0:
        original_print("\n⏱ AVG TIME")

        if mode in ["txt2sql", "both"]:
            original_print(
                f"Txt2SQL : "
                f"{time_stats['t2sql']/stats['total']:.4f}s"
            )

        original_print(
            f"SQL Exec: "
            f"{time_stats['sql_exec']/stats['total']:.4f}s"
        )

        if mode in ["sql2txt", "both"]:
            original_print(
                f"SQL2Text: "
                f"{time_stats['sql2text']/stats['total']:.4f}s"
            )

        original_print(f"Failed indices: {failed_indices}")

        original_print(f"Metric counts: {metric_counts}")
        
    # =========================================================
    # SAVE LOG
    # =========================================================
    if save_log:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        path = f"log_{mode}_{ts}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "mode": mode,
                    "stats": stats,
                    "logs": logs,
                    "failed_cases": failed_cases,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        PRED_PATH = f"data.jsonl"

        with open(PRED_PATH, "w", encoding="utf-8") as f:
            for item in pred_cases:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        print(f"\n💾 Saved: {path}")


# =========================================================
# CLI
# =========================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        type=str,
        default="both",
        choices=["txt2sql", "sql2txt", "both"],
        help="Evaluation mode",
    )

    parser.add_argument(
        "--file",
        type=str,
        default=DATA_TEST_PATH,
    )

    parser.add_argument(
        "--retry",
        type=int,
        default=1,
    )

    args = parser.parse_args()

    with app.app_context():
        run_test(
            file_path=args.file,
            mode=args.mode,
            retry=args.retry,
        )