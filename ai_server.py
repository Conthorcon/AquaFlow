"""Standalone AI service. No database access or web-app imports."""
import hmac
import os
from pathlib import Path
from threading import Lock

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

ROOT = Path(__file__).resolve().parent
inference_lock = Lock()


def run_chatbot(message):
    from src.chatbot.src.txt2sql import generate_sql
    return generate_sql(message)


def run_ocr(file_storage):
    import numpy as np
    from PIL import Image, UnidentifiedImageError
    from src.ocr.text_det import get_detections
    from src.ocr.text_reg import predict_detections
    from utils.parser import InvoiceParser
    try:
        with Image.open(file_storage.stream) as image:
            pixels = np.array(image.convert("RGB"))
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        from werkzeug.exceptions import BadRequest
        raise BadRequest("Invalid image") from exc
    model_path = os.environ.get("OCR_MODEL_PATH", str(ROOT / "models/checkpoints/detect_text/best.pt"))
    detections = get_detections(pixels, model_path=model_path)
    return InvoiceParser().extract_fields(predict_detections(detections))


def create_app():
    app = Flask(__name__)
    key = os.environ.get("AI_API_KEY", "")
    if not key:
        raise RuntimeError("Set AI_API_KEY before starting the AI server")
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

    @app.before_request
    def authenticate():
        if request.path != "/health" and not hmac.compare_digest(
            request.headers.get("Authorization", "").encode(), f"Bearer {key}".encode()
        ):
            return jsonify(error="Unauthorized"), 401

    @app.get("/health")
    def health():
        # Liveness only: models are loaded on their first request.
        return jsonify(status="ok")

    @app.post("/api/chatbot/ask")
    def chatbot():
        data = request.get_json(silent=True)
        message = data.get("message") if isinstance(data, dict) else None
        if not isinstance(message, str) or not message.strip() or len(message) > 8000:
            return jsonify(error="message must contain 1-8000 characters"), 400
        with inference_lock:
            result = run_chatbot(message)
        return jsonify(response=result)

    @app.post("/api/ocr/extract")
    def ocr():
        if "file" not in request.files:
            return jsonify(error="Missing file"), 400
        with inference_lock:
            result = run_ocr(request.files["file"])
        return jsonify(result)

    @app.errorhandler(Exception)
    def error(exc):
        if isinstance(exc, HTTPException):
            return jsonify(error=exc.description), exc.code
        app.logger.exception("AI inference failed")
        return jsonify(error="AI inference failed"), 500

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=4850, debug=False)
