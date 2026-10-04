import csv
import io
import re
import difflib
# import pytesseract
from PIL import Image
from src.database.models import Customer, Product


def fuzzy_match(query, choices, threshold=0.6):
    """Sử dụng difflib để tìm kết quả gần đúng nhất."""
    if not query:
        return None
    matches = difflib.get_close_matches(query, choices.keys(), n=1, cutoff=threshold)
    return choices[matches[0]] if matches else None

def get_product_choices():
    products = Product.query.all()
    # Tạo map { "Tên - Nắp - Loại - Dung tích": ID }
    return {f"{p.name} {p.cap_type} {p.bottle_type} {p.capacity}".strip(): p.id for p in products}

def get_customer_choices():
    customers = Customer.query.all()
    return {c.name.strip(): c.id for c in customers}

def parse_csv_data(file_storage):
    """Xử lý file CSV."""
    stream = io.StringIO(file_storage.stream.read().decode("UTF8"), newline=None)
    reader = csv.DictReader(stream)
    
    extracted_data = {
        "customer": None,
        "items": []
    }

    customer_choices = get_customer_choices()
    product_choices = get_product_choices()
    
    for row in reader:
        # Giả định format: Khách hàng, Sản phẩm, Số lượng
        cust_name = row.get("Khách hàng") or row.get("Customer")
        prod_name = row.get("Sản phẩm") or row.get("Product")
        qty = row.get("Số lượng") or row.get("Quantity") or 1
        
        if cust_name and not extracted_data["customer"]:
            extracted_data["customer"] = {
                "name": cust_name,
                "id": fuzzy_match(cust_name, customer_choices)
            }
            
        if prod_name:
            extracted_data["items"].append({
                "name": prod_name,
                "qty": int(qty),
                "id": fuzzy_match(prod_name, product_choices)
            })
    

    return extracted_data

import src.ocr.text_reg as reg 
import src.ocr.text_det as det
import json
from utils.parser import InvoiceParser 
import numpy as np
import matplotlib.pyplot as plt

def parse_ocr_data(file_storage):
    # 1. Phát hiện các cụm chữ (YOLO)
    # Trả về: List[{"crop": PIL.Image, "box": [x1, y1, x2, y2]}]
    img = np.array(Image.open(file_storage.stream))
    # print("Ok")
    print(type(img), img.shape)
    detections = det.get_detections(img)
    
    # 2. Nhận diện chữ (OCR)
    # Trả về: List[{"text": str, "box": list}]
    ocr_results = reg.predict_detections(detections)
    
    # 3. Parse các trường thông tin
    parser = InvoiceParser()
    extracted_data = parser.extract_fields(ocr_results)
    
    # In kết quả
    print("\n--- Kết quả trích xuất ---")
    print(json.dumps(extracted_data, indent=4, ensure_ascii=False))

    customer_choices = get_customer_choices()
    product_choices = get_product_choices()
    
    pids = []

    cid = fuzzy_match(extracted_data["customer"], customer_choices, threshold=0.8)
    for item in extracted_data["items"]:
        pid = fuzzy_match(item["product"], product_choices, threshold=0.5)
        pids.append(pid)


    results = {
        "customer": {"name": extracted_data["customer"], "id": cid}, 
        "items": [ {"name": item["product"], "qty": item["quantity"], "id": pid} for item, pid in zip(extracted_data["items"], pids)]
    }

    return results

# def parse_ocr_data(file_storage):
#     """Xử lý ảnh bằng Tesseract OCR."""
#     # Đọc ảnh
#     img = Image.open(file_storage.stream)
    
#     extracted_data = {
#         "customer": None,
#         "items": []
#     }
    
#     # OCR ảnh -> text
#     text = pytesseract.image_to_string(img, lang='vie+eng')

#     customer_choices = get_customer_choices()
#     product_choices = get_product_choices()

#     # Logic tách dòng đơn giản
#     lines = response.split('\n')
#     for line in lines:
#         line = line.strip()
#         if not line: continue
        
#         # Tìm số lượng (thường là số cuối dòng hoặc sau tên sản phẩm)
#         qty_match = re.search(r'(\d+)\s*$', line)
#         qty = int(qty_match.group(1)) if qty_match else 1
#         clean_text = re.sub(r'\d+\s*$', '', line).strip()
        
#         # Thử khớp với khách hàng nếu chưa có
#         if not extracted_data["customer"]:
#             # Thường tên khách hàng ở mấy dòng đầu
#             cid = fuzzy_match(clean_text, customer_choices, threshold=0.8)
#             if cid:
#                 extracted_data["customer"] = {"name": clean_text, "id": cid}
#                 continue
        
#         # Khớp với sản phẩm
#         pid = fuzzy_match(clean_text, product_choices, threshold=0.5)
#         if pid:
#             extracted_data["items"].append({
#                 "name": clean_text,
#                 "qty": qty,
#                 "id": pid
#             })
            
#     return extracted_data
