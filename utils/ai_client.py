"""HTTP boundary between the web application and the private AI service."""
import os

import requests


class AIServiceError(RuntimeError):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def _post(path, **kwargs):
    base = os.environ.get("AI_SERVER_URL", "http://127.0.0.1:4850").rstrip("/")
    key = os.environ.get("AI_API_KEY", "")
    try:
        response = requests.post(
            base + path,
            headers={"Authorization": f"Bearer {key}"},
            timeout=(5, float(os.environ.get("AI_TIMEOUT_SECONDS", "180"))),
            **kwargs,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Expected an object")
        return data
    except requests.Timeout as exc:
        raise AIServiceError("Server AI phản hồi quá chậm. Vui lòng thử lại.", 504) from exc
    except (requests.RequestException, ValueError) as exc:
        raise AIServiceError("Không thể nhận kết quả từ server AI.") from exc


def ask_ai(message):
    data = _post("/api/chatbot/ask", json={"message": message})
    if not isinstance(data.get("response"), str):
        raise AIServiceError("Kết quả chatbot không hợp lệ.")
    return data["response"]


def extract_invoice(file_storage):
    data = _post("/api/ocr/extract", files={
        "file": (file_storage.filename or "invoice", file_storage.stream,
                 file_storage.mimetype or "application/octet-stream")
    })
    if not isinstance(data.get("customer"), (str, type(None))) or not isinstance(data.get("items"), list):
        raise AIServiceError("Kết quả OCR không hợp lệ.")
    for item in data["items"]:
        if not isinstance(item, dict) or not isinstance(item.get("product"), str) or not isinstance(item.get("quantity"), (int, float)):
            raise AIServiceError("Kết quả OCR không hợp lệ.")
    return data
