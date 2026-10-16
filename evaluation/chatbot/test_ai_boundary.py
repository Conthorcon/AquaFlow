"""Run: python -m unittest test_ai_boundary -v (no model downloads)."""
import io
import os
import sys
import threading
import unittest
from unittest.mock import patch

import requests
from werkzeug.datastructures import FileStorage
from werkzeug.serving import make_server

from ai_server import create_app
from utils.ai_client import AIServiceError, ask_ai, extract_invoice


class AIBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"AI_API_KEY": "test-key"})
        self.env.start()
        self.server = make_server("127.0.0.1", 0, create_app())
        os.environ["AI_SERVER_URL"] = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        self.env.stop()

    def test_chat_over_http(self):
        with patch("ai_server.run_chatbot", return_value="SELECT 1;") as model:
            self.assertEqual(ask_ai("Doanh thu?"), "SELECT 1;")
            model.assert_called_once_with("Doanh thu?")

    def test_ocr_multipart_and_database_mapping(self):
        from utils.import_logic import parse_ocr_data
        result = {"customer": "An", "items": [{"product": "Water", "quantity": 2}]}
        def infer(upload):
            self.assertEqual(upload.read(), b"image-content")
            return result
        with patch("ai_server.run_ocr", side_effect=infer), patch(
            "utils.import_logic.get_customer_choices", return_value={"An": 7}
        ), patch("utils.import_logic.get_product_choices", return_value={"Water": 9}):
            data = parse_ocr_data(FileStorage(stream=io.BytesIO(b"image-content"), filename="a.png"))
        self.assertEqual(data["customer"]["id"], 7)
        self.assertEqual(data["items"], [{"name": "Water", "qty": 2, "id": 9}])

    def test_auth_validation_and_errors(self):
        client = create_app().test_client()
        self.assertEqual(client.post("/api/chatbot/ask", json={"message": "hi"}).status_code, 401)
        headers = {"Authorization": "Bearer test-key"}
        self.assertEqual(client.post("/api/chatbot/ask", json=[], headers=headers).status_code, 400)
        self.assertEqual(client.post("/api/ocr/extract", headers=headers).status_code, 400)
        with patch("ai_server.run_chatbot", side_effect=RuntimeError("private detail")):
            with self.assertRaises(AIServiceError) as error:
                ask_ai("hi")
            self.assertEqual(error.exception.status_code, 502)
            self.assertNotIn("private detail", str(error.exception))

    def test_timeout(self):
        with patch("utils.ai_client.requests.post", side_effect=requests.Timeout):
            with self.assertRaises(AIServiceError) as error:
                ask_ai("hi")
        self.assertEqual(error.exception.status_code, 504)

    def test_web_routes_without_ai_libraries(self):
        from app import app
        self.assertFalse(any(name in sys.modules for name in ("torch", "transformers", "PIL", "ultralytics")))
        client = app.test_client()
        self.assertEqual(client.get("/login").status_code, 200)
        with client.session_transaction() as session:
            session["user_id"] = 1
        with patch("ai_server.run_chatbot", return_value="SELECT 1;"):
            response = client.post("/api/chatbot/ask", json={"message": "hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"response": "SELECT 1;"})
        with patch("utils.ai_client.requests.post", side_effect=requests.ConnectionError):
            self.assertEqual(client.post("/api/chatbot/ask", json={"message": "hello"}).status_code, 502)
            response = client.post("/api/sale/extract", data={"file": (io.BytesIO(b"x"), "a.png")})
            self.assertEqual(response.status_code, 502)


if __name__ == "__main__":
    unittest.main()
