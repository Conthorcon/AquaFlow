# Chạy web và AI riêng

Web giữ database, đăng nhập, CSV và đối chiếu khách hàng/sản phẩm. Web gọi AI qua HTTP từ backend; trình duyệt không nhận API key. AI không truy cập database. Chatbot hiện trả SQL, chưa thực thi SQL.

## Cài đặt (Python 3.11)

Trên máy web:

```powershell
python -m venv .venv-web
.\.venv-web\Scripts\python.exe -m pip install -r requirements.txt
```

Trên máy AI, dùng cùng source project:

```powershell
python -m venv .venv-ai
.\.venv-ai\Scripts\python.exe -m pip install -r requirements-ai.txt
```

Model OCR mặc định: `models/checkpoints/detect_text/best.pt`.
Adapter chatbot mặc định: `src/chatbot/finetune/checkpoints/deepseek/txt2sql_fullv2_550` (cần adapter_config.json và adapter_model.safetensors). Những file model bị gitignore nên phải chuyển riêng sang máy AI.
Model nền Hugging Face và trọng số VietOCR có thể được tải ở lần gọi đầu. Cần Internet và RAM/VRAM đủ. Model chatbot nạp lười và giữ trong bộ nhớ; OCR vẫn dùng cơ chế nạp model của code OCR hiện có. Một tiến trình AI xử lý lần lượt các yêu cầu suy luận để tránh chạy đồng thời trên GPU.

## Chạy local: hai terminal

Terminal AI, từ thư mục gốc project:

```powershell
$env:AI_API_KEY="thay-bang-chuoi-bi-mat-dai"
.\.venv-ai\Scripts\python.exe ai_server.py
```

Terminal web, từ thư mục gốc project:

```powershell
$env:AI_API_KEY="thay-bang-chuoi-bi-mat-dai"
$env:AI_SERVER_URL="http://127.0.0.1:4850"
$env:AI_TIMEOUT_SECONDS="180"
.\.venv-web\Scripts\python.exe -m flask --app app run --port 4849 --no-reload
```

Hai API key phải giống nhau. Có thể dùng `.venv` hiện có thay cho hai môi trường mới khi kiểm tra local. Biến môi trường phải đặt trong đúng terminal chạy từng server; không tự đọc `.env`.

Mở http://127.0.0.1:4849. `GET http://127.0.0.1:4850/health` chỉ kiểm tra tiến trình sống, không xác nhận model đã nạp thành công.

## Máy AI riêng

Chạy bằng WSGI server thay cho Flask development server:

```powershell
$env:AI_API_KEY="thay-bang-chuoi-bi-mat-dai"
.\.venv-ai\Scripts\waitress-serve.exe --host=0.0.0.0 --port=4850 --call ai_server:create_app
```

Đặt reverse proxy HTTPS phía trước nếu gọi qua Internet. Trên web đặt `AI_SERVER_URL=https://ai.example.com` và cùng `AI_API_KEY` qua cấu hình môi trường của host. Không dùng localhost khi hai server ở hai máy khác nhau. Không commit API key.

Các biến tùy chọn trên AI: `AI_BASE_MODEL`, `AI_LORA_PATH`, `OCR_MODEL_PATH` (nên dùng đường dẫn tuyệt đối cho model tùy chỉnh). Giới hạn upload AI: 10 MiB. Web trả 502 khi AI lỗi/không kết nối được, 504 khi timeout. Timeout không hủy tác vụ đang chạy trên AI.

## API nội bộ

- `POST /api/chatbot/ask`: JSON `{"message":"..."}` → `{"response":"..."}`.
- `POST /api/ocr/extract`: multipart trường `file` → dữ liệu parser với `customer`, `items` (`product`, `quantity`).
- Cả hai cần header `Authorization: Bearer <AI_API_KEY>`.

## Kiểm tra

```powershell
.\.venv-web\Scripts\python.exe -m unittest test_ai_boundary -v
```

Kiểm tra HTTP thật giữa client và server cục bộ với inference giả lập; không tải/chạy model. Cần kiểm tra suy luận thật riêng trên máy AI. requirements-ai.txt kế thừa phiên bản thư viện AI trước khi tách; việc cài môi trường AI sạch và tương thích checkpoint cần được xác nhận trên máy đích.

Việc tách AI chưa hoàn tất deploy Vercel: web vẫn dùng SQLite local, cần chuyển database lưu bền vững và cấu hình hosting riêng.
