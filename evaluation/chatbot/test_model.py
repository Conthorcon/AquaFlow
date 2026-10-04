import json
import sqlite3
import pandas as pd
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import random

from chatbot import txt2sql

# ===== CONFIG =====
DB_PATH = "/home/truongkhanh/work/agent/AquaSupplyAI/chatbot/instance/aquasupply.db"
DATA_PATH = "/home/truongkhanh/work/agent/AquaSupplyAI/chatbot/finetune/dataset/train/sql2txt_fullv2.jsonl"  # dataset của bạn
SIM_THRESHOLD = 0.8

# ===== LOAD MODEL EMBEDDING =====
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# ===== HELPER =====
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

# ===== LOAD DATA =====
def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

# ===== MAIN EVAL =====
def evaluate(model_infer_fn):

    data = load_jsonl(DATA_PATH)

    conn = sqlite3.connect(DB_PATH)

    metrics = {
        "sql_exact_match": 0,
        "execution_acc": 0,
        "result_match": 0,
        "semantic_sim": [],
        "final_acc": 0
    }

    logs = []


    accs = []

    random.seed(2026)
    data = random.sample(data, 100)

    for item in tqdm(data):
        question = item["input"]["question"]
        gt_sql = item["input"]["query"]
        gt_result = item["input"]["result"]
        gt_answer = item["output"]


        # ===== MODEL PREDICT =====
        pred_sql = model_infer_fn(question)

        # ===== SQL EXACT MATCH =====
        em = exact_match(pred_sql, gt_sql)
        metrics["sql_exact_match"] += em

        # ===== EXECUTION =====
        pred_res, ok1 = execute_sql(conn, pred_sql)
        gt_res, ok2 = execute_sql(conn, gt_sql)

        exec_acc = int(ok1 and ok2 and pred_res == gt_res)
        metrics["execution_acc"] += exec_acc

        # ===== RESULT MATCH =====
        res_match = compare_result(pred_res, gt_res)
        metrics["result_match"] += res_match

        # ===== SEMANTIC SIM =====
        # (giả sử bạn có model sinh answer hoặc dùng template)
        pred_answer = str(pred_res) if pred_res else ""

        sim = semantic_similarity(pred_answer, gt_answer)
        metrics["semantic_sim"].append(sim)

        final = int(sim > SIM_THRESHOLD)
        metrics["final_acc"] += final

        logs.append({
            "question": question,
            "gt_sql": gt_sql,
            "pred_sql": pred_sql,
            "exec_acc": exec_acc,
            "semantic_sim": sim
        })

        accs.append(sim)

    # ===== AGGREGATE =====
    n = len(data)
    results = {
        "SQL Exact Match": metrics["sql_exact_match"] / n,
        "Execution Accuracy": metrics["execution_acc"] / n,
        "Result Match": metrics["result_match"] / n,
        "Avg Semantic Similarity": sum(metrics["semantic_sim"]) / n,
        "Final Accuracy": metrics["final_acc"] / n
    }

    save_path = "log/eval_log.csv"

    df = pd.DataFrame(logs)
    df.to_csv(save_path, index=False)

    print(sum(accs) / len(accs))
    print(results)
    return results

# try:
evaluate(txt2sql.predict_sql_query)
# except Exception as e:
#     print(e)