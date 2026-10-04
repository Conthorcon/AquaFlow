import requests
from fastapi import FastAPI, Request
import json
import sql2txt as s2t

app = FastAPI()

BOT_TOKEN = "3431117687435998990:oVWhauqbbdMqVhGpaGoFdxjZvckbQVPuJPqzUJUGSqEQDLsqQEidVsxdXyVryVTm"
URL = f"https://bot-api.zaloplatforms.com/bot{BOT_TOKEN}"

def send_message(user_id, message):
    url = f"{URL}/sendMessage"

    payload = {
    "chat_id": user_id,
    "text": message
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

def handle_message(user_id, user_name, text):
    text_lower = text.strip().lower()
    
    # 1. Kiểm tra xác nhận
    if text_lower == "xác nhận":
        payload = {"zalo_user_id": str(user_id), "user_name": user_name}
        try:
            resp = requests.post("http://127.0.0.1:4849/api/zalo_order/confirm", json=payload)
            print(resp)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    return "Khách hàng đã chốt đơn thành công, cảm ơn!"
                elif data.get("status") == "not_found":
                    return "Bạn chưa có đơn hàng nào chờ xác nhận hoặc chưa được quản lý duyệt."
                else:
                    return f"Lỗi chốt đơn trên hệ thống: {data.get('message', '')}"
            else:
                return "Hệ thống đang lỗi, vui lòng thử lại sau."
        except Exception as e:
            print("Exception:", e)
            return "Hệ thống đang bận. Vui lòng thử lại sau."

    # 2. Xử lý tin nhắn order (kết quả trả về dạng json chuỗi từ LLM)
    order_json_str = s2t.order_product(text)
    print(order_json_str)
    
    try:
        order_json_str = order_json_str.strip()
        if order_json_str.startswith("```json"):
            order_json_str = order_json_str[7:-3]
        elif order_json_str.startswith("```"):
            order_json_str = order_json_str[3:-3]
            
        order = json.loads(order_json_str)
        order["is_order"] = True
    except Exception as e:
        print("Lỗi parse JSON:", e, "Dữ liệu:", order_json_str)
        return "Xin lỗi tôi không hiểu yêu cầu của bạn"

    if order.get("is_order"):
        payload = {
            "zalo_user_id": str(user_id),
            "order_data": order
        }
        try:
            resp = requests.post("http://127.0.0.1:4849/api/zalo_order/add", json=payload)
            if resp.status_code == 200:
                return "Đã gửi đơn hàng cho Quản lý cửa hàng tạo. Vui lòng đợi quản lý chốt đơn trước khi xác nhận!"
            else:
                return "Lỗi gửi đơn lên hệ thống."
        except Exception as e:
            print("API Error:", e)
            return "Máy chủ đang bận. Bạn vui lòng đợi chút rồi nhắn lại."
    else:
        return "Xin lỗi tôi không hiểu yêu cầu của bạn"

# 👉 Webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("Received:", data)

    try:
        event = data.get("event_name")

        if event == "message.text.received":
            message = data["message"]
            user_id = message["chat"]["id"]
            user_name = message["from"]["display_name"]
            text = message["text"]

            # xử lý
            reply = handle_message(user_id, user_name, text)

            # gửi lại
            send_message(user_id, reply)

    except Exception as e:
        print("Error:", e)

    return {"status": "ok"}



# Lệnh test (sẽ print chuỗi order)
# print(handle_message("123", "cho tôi 2 chai nước suối lavie"))
