from flask import Blueprint, request, jsonify, session
from utils.import_logic import parse_csv_data, parse_ocr_data
from src.database.models import db, Sale, SaleItem, Customer, Product, ProductPriceConfig
from datetime import datetime

sale_import_bp = Blueprint('sale_import', __name__)

@sale_import_bp.route('/api/sale/extract', methods=['POST'])
def extract_data():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Không tìm thấy file"}), 400
    
    file = request.files['file']
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.csv'):
            data = parse_csv_data(file)
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.webp')):
            data = parse_ocr_data(file)
        else:
            return jsonify({"status": "error", "message": "Định dạng file không hỗ trợ"}), 400
            
        return jsonify(data)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@sale_import_bp.route('/api/sale/bulk-create', methods=['POST'])
def bulk_create():
    data = request.get_json()
    cust_id = data.get('customer_id')
    items = data.get('items', [])
    
    if not cust_id or not items:
        return jsonify({"status": "error", "message": "Dữ liệu không hợp lệ"}), 400
        
    try:
        customer = Customer.query.get(cust_id)
        if not customer:
            return jsonify({"status": "error", "message": "Khách hàng không tồn tại"}), 404
            
        new_sale = Sale(
            customer_id=cust_id,
            total_amount=0,
            status="pending",
            note="Nhập từ file/ảnh"
        )
        db.session.add(new_sale)
        
        total = 0
        for item in items:
            p_id = item.get('product_id')
            qty = int(item.get('qty', 1))
            
            # Lấy giá dựa trên loại khách hàng
            price_cfg = ProductPriceConfig.query.filter_by(
                product_id=p_id, 
                group_id=customer.group_id
            ).first()
            
            price = price_cfg.price if price_cfg else 0
            
            sale_item = SaleItem(
                sale=new_sale,
                product_id=p_id,
                quantity=qty,
                price_at_sale=price
            )
            db.session.add(sale_item)
            total += price * qty
            
        new_sale.total_amount = total
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Tạo hóa đơn thành công", "sale_id": new_sale.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
