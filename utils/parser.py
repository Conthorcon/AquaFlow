import re
import difflib


class InvoiceParser:
    def __init__(self):
        self.anchors = {
            "date": ["ngày tạo", "ngày in"],
            "buyer": ["bên mua", "khách hàng"],
            "tax": ["thuế"],
            "total": ["tổng cộng", "thành tiền"],
            "table_headers": ["sản phẩm", "sl", "đơn giá", "thành tiền"]
        }

    def group_by_rows(self, ocr_results, y_threshold=15):
        """Nhóm các cụm chữ có tọa độ Y gần nhau thành một hàng."""
        if not ocr_results:
            return []
            
        # Sắp xếp theo Y trước
        sorted_results = sorted(ocr_results, key=lambda x: x["box"][1])
        
        rows = []
        current_row = [sorted_results[0]]
        
        for i in range(1, len(sorted_results)):
            prev_y_center = (current_row[-1]["box"][1] + current_row[-1]["box"][3]) / 2
            curr_y_center = (sorted_results[i]["box"][1] + sorted_results[i]["box"][3]) / 2
            
            if abs(curr_y_center - prev_y_center) < y_threshold:
                current_row.append(sorted_results[i])
            else:
                # Sắp xếp hàng theo X
                rows.append(sorted(current_row, key=lambda x: x["box"][0]))
                current_row = [sorted_results[i]]
        
        rows.append(sorted(current_row, key=lambda x: x["box"][0]))
        return rows

    def detect_columns(self, header_row):
        """Khung các cột dựa trên tọa độ trung tâm X của các nhãn trong header."""
        cols = {}
        for item in header_row:
            text = item["text"].lower()
            x_center = (item["box"][0] + item["box"][2]) / 2
            
            if "sản phẩm" in text or "sản phảm" in text or "tên hhdv" in text:
                cols["product"] = x_center
            elif "sl" in text or "số lượng" in text or "số" in text:
                cols["quantity"] = x_center
            elif "đơn giá" in text or "giá" in text:
                cols["price"] = x_center
            elif "thành tiền" in text or "thanh tien" in text:
                cols["total"] = x_center
        return cols

    def is_end_of_table(self, row_text_lower):
        """Xác định dòng báo hiệu kết thúc danh sách sản phẩm."""
        end_keywords = ["tổng cộng", "thuế", "tam tính", "tạm tính", "cộng"]
        if any(kw in row_text_lower for kw in end_keywords) and "sản phẩm" not in row_text_lower:
            return True
        return False

    def extract_fields(self, ocr_results):
        rows = self.group_by_rows(ocr_results)
        
        data = {
            "date": None,
            "customer": None,
            "phone": None,
            "address": None,
            "items": [],
            "tax": None,
            "total_amount": None
        }
        
        header_row_index = -1
        columns_map = {}
        
        for i, row in enumerate(rows):
            row_text = " ".join([item["text"] for item in row])
            row_text_lower = row_text.lower()
            
            # 1. Extraction Date
            if "ngày tạo" in row_text_lower:
                match = re.search(r"\d{1,2}/\d{1,2}/\d{4}", row_text)
                if match:
                    data["date"] = match.group()
            
            # 2. Extraction Customer Info (Bên mua)
            if "bên mua" in row_text_lower:
                buyer_x = next((it["box"][0] for it in row if "bên mua" in it["text"].lower()), 0)
                
                if i + 1 < len(rows):
                    next_row = rows[i+1]
                    buyer_info = [it["text"] for it in next_row if abs(it["box"][0] - buyer_x) < 200]
                    data["customer"] = " ".join(buyer_info)
                
                for j in range(i+1, min(i+5, len(rows))):
                    search_row = rows[j]
                    search_text = " ".join([it["text"] for it in search_row if abs(it["box"][0] - buyer_x) < 200])
                    
                    if not data["phone"]:
                        phone_match = re.search(r"0\d{9,10}", search_text)
                        if phone_match:
                            data["phone"] = phone_match.group()
                    
                    if not data["address"] and ("quận" in search_text.lower() or "đường" in search_text.lower() or "tp" in search_text.lower()):
                        data["address"] = search_text

            # 3. Extraction Tax
            if "thuế" in row_text_lower:
                data["tax"] = row_text.split(":")[-1].strip() if ":" in row_text else row_text

            # 4. Extraction Total Amount
            if "tổng cộng" in row_text_lower or "thành tiền" in row_text_lower:
                if "tổng cộng" in row_text_lower:
                    amount_match = re.search(r"[\d\.,]+d|[\d\.,]+đ", row_text)
                    if amount_match:
                        data["total_amount"] = amount_match.group()
                    elif i + 1 < len(rows):
                        next_row_text = " ".join([item["text"] for item in rows[i+1]])
                        amount_match = re.search(r"[\d\.,]+d|[\d\.,]+đ", next_row_text)
                        if amount_match:
                            data["total_amount"] = amount_match.group()

            # 5. Table Header Detection
            if "sản phẩm" in row_text_lower and ("sl" in row_text_lower or "đơn giá" in row_text_lower or "thành tiền" in row_text_lower):
                header_row_index = i
                columns_map = self.detect_columns(row)

        # 6. Coordinate-Based Table Extraction (Pass 2)
        if header_row_index != -1 and columns_map:
            for i in range(header_row_index + 1, len(rows)):
                row_text = " ".join([item["text"] for item in rows[i]])
                row_text_lower = row_text.lower()
                
                if self.is_end_of_table(row_text_lower):
                    break
                    
                if not row_text.strip():
                    continue

                item_data = {"product": [], "quantity": [], "price": [], "total": []}
                
                for item in rows[i]:
                    x_center = (item["box"][0] + item["box"][2]) / 2
                    text = item["text"]
                    
                    closest_col = None
                    min_dist = float('inf')
                    for col_name, col_x in columns_map.items():
                        dist = abs(x_center - col_x)
                        
                        if col_name == "product" and x_center > col_x and (x_center - col_x) < 300:
                            dist = dist * 0.5 

                        if dist < min_dist:
                            min_dist = dist
                            closest_col = col_name
                            
                    if closest_col and min_dist < 400: 
                        item_data[closest_col].append(text)
                
                prod_str = " ".join(item_data["product"]).strip()
                qty_str = " ".join(item_data["quantity"]).strip()
                price_str = " ".join(item_data["price"]).strip()
                total_str = " ".join(item_data["total"]).strip()
                
                if prod_str or qty_str or price_str or total_str:
                    qty_cleaned = "".join([c for c in qty_str if c.isdigit() or c == '.' or c == ','])
                    data["items"].append({
                        "product": prod_str,
                        "quantity": qty_cleaned if qty_cleaned else qty_str,
                        "price": price_str,
                        "total": total_str
                    })

        return data
