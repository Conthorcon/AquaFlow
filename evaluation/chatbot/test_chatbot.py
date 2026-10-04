from chatbot.txt2sql import predict_sql_query
from chatbot.sql2txt import query_data, predict_answer
import time
import json
import random
import os


with open("chatbot/finetune/dataset/train/sql2txt_full.jsonl", "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f if line.strip()]

indices = random.sample(range(0, len(data)), 20)

os.makedirs("log", exist_ok=True)

with open("log/test_chatbot.txt", "w", encoding="utf-8") as f:

    for i, index in enumerate(indices):
        start = time.time()
        f.write(f"\n\n=== TEST {i+1} ===\n")
        test_data = data[index]  
        question = test_data["input"]["question"]
        sql_seq = test_data["input"]["query"]
        ans = test_data["output"]   
        f.write(f"# Input #\n")
        f.write(f"Question: {question}\n")
        f.write(f"SQL Query: {sql_seq}\n")
        f.write(f"Answer: {ans}\n")

        f.write("\n# Predict #\n")
        # TXT2SQL
        sql_seq = predict_sql_query(question)
        
        # SQL Query
        try:
            sql = query_data(sql_seq)
        except Exception as e:
            sql = f"Error: {e}"

        # SQL2TXT
        ans = predict_answer(question, sql_seq, sql)

        f.write(f"Question: {question}\n")
        f.write(f"SQL Query: {sql_seq}\n")
        f.write(f"SQL: {sql}\n")
        f.write(f"Answer: {ans}\n")
        f.write(f"Time: {time.time() - start}\n")



    



