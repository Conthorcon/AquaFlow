import csv
import io
import re
import difflib
# import pytesseract
from utils.ai_client import extract_invoice
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

def parse_ocr_data(file_storage):
    extracted_data = extract_invoice(file_storage)
    customer_choices = get_customer_choices()
    product_choices = get_product_choices()
    return {
        "customer": {
            "name": extracted_data["customer"],
            "id": fuzzy_match(extracted_data["customer"], customer_choices, threshold=0.8),
        },
        "items": [
            {
                "name": item["product"],
                "qty": item["quantity"],
                "id": fuzzy_match(item["product"], product_choices, threshold=0.5),
            }
            for item in extracted_data["items"]
        ],
    }
