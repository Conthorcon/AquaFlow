
# QUERY BOT
## SETUP
- dataset:
    - TXT2SQL
        - txt2sql without outliner 
            - Không xử lý được các trường hợp câu hỏi không phải câu truy vấn
        - txt2sql with outliner 
            - Bị duplicate nhiều
        - txt2sql with outliner and non-dup
            - 
    - SQL2TXT
        - sql2txt without outliner 
        - sql2txt with outliner 
        - sql2txt with outliner and non-dup
- model:
    TXT2SQL
        - deepseek-ai/deepseek-coder-1.3b-instruct
    SQL2TXT
        - meta-llama/Llama-3.2-1B-Instruct

## TEST
- [28/04 5:00] Test 20 câu query trong tập sql2txt_full.jsonl 
    - Đúng: 2
    - Sai: 18
    - Nhận xét: Sai chủ yếu do dùng các trường truy vấn không có