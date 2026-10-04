from flask import Blueprint, render_template, request, jsonify
from src.database.models import db, Purchase, PurchaseCategory
from datetime import datetime

purchase_bp = Blueprint('purchase', __name__)

@purchase_bp.route('/purchase')
def index():
    # Seed initial categories if empty
    if PurchaseCategory.query.count() == 0:
        defaults = ['Nguyên liệu', 'Văn phòng', 'Vận hành', 'Khác']
        for name in defaults:
            db.session.add(PurchaseCategory(name=name))
        db.session.commit()
    return render_template('purchase.html')

@purchase_bp.route('/api/purchaseList')
def get_purchase_list():
    query_str = request.args.get('q', '')
    mode = request.args.get('mode', 'all')
    f_day = request.args.get('day', '')
    f_month = request.args.get('month', '')
    f_year = request.args.get('year', '')
    f_cat = request.args.get('category', '')
    
    query = Purchase.query
    
    # 1. Search by description
    if query_str:
        query = query.filter(Purchase.description.contains(query_str))
    
    # 2. Filter by Category
    if f_cat:
        query = query.filter(Purchase.category == f_cat)
        
    # 3. Filter by Time (if mode is 'time')
    if mode == 'time':
        now = datetime.now()
        # Default to current values if empty
        try:
            day = int(f_day) if f_day else None
            month = int(f_month) if f_month else now.month
            year = int(f_year) if f_year else now.year
            
            if year:
                query = query.filter(db.extract('year', Purchase.date) == year)
            if month:
                query = query.filter(db.extract('month', Purchase.date) == month)
            if day:
                query = query.filter(db.extract('day', Purchase.date) == day)
        except (ValueError, TypeError):
            pass
            
    purchases = query.order_by(Purchase.date.desc()).all()
    
    result = []
    for p in purchases:
        result.append({
            "id": p.id,
            "description": p.description,
            "total_amount": p.total_amount,
            "category": p.category,
            "date": p.date.strftime("%d/%m/%Y %H:%M")
        })
        
    return jsonify(result)

@purchase_bp.route('/api/purchase/add', methods=['POST'])
def add_purchase():
    data = request.get_json()
    
    try:
        new_purchase = Purchase(
            description=data.get('description'),
            total_amount=float(data.get('total_amount', 0)),
            category=data.get('category', 'Khác'),
            date=datetime.now() # Use server time for now
        )
        
        db.session.add(new_purchase)
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Thêm đơn mua hàng thành công"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@purchase_bp.route('/api/purchase/update', methods=['POST'])
def update_purchase():
    data = request.get_json()
    p_id = data.get('id')
    
    if not p_id:
        return jsonify({"status": "error", "message": "Thiếu mã đơn hàng"}), 400
        
    purchase = Purchase.query.get_or_404(p_id)
    
    try:
        purchase.description = data.get('description')
        purchase.total_amount = float(data.get('total_amount', 0))
        purchase.category = data.get('category', 'Khác')
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Cập nhật đơn hàng thành công"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@purchase_bp.route('/api/purchase/delete/<int:p_id>', methods=['DELETE'])
def delete_purchase(p_id):
    purchase = Purchase.query.get_or_404(p_id)
    try:
        db.session.delete(purchase)
        db.session.commit()
        return jsonify({"status": "success", "message": "Đã xóa đơn mua hàng"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

# Purchase Category Management
@purchase_bp.route('/api/purchaseCategories')
def get_categories():
    categories = PurchaseCategory.query.all()
    return jsonify([{"id": c.id, "name": c.name} for c in categories])

@purchase_bp.route('/api/purchaseCategory/add', methods=['POST'])
def add_category():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({"status": "error", "message": "Thiếu tên phân loại"}), 400
    
    if PurchaseCategory.query.filter_by(name=name).first():
        return jsonify({"status": "error", "message": "Phân loại này đã tồn tại"}), 400

    try:
        new_cat = PurchaseCategory(name=name)
        db.session.add(new_cat)
        db.session.commit()
        return jsonify({"status": "success", "message": "Thêm phân loại thành công", "id": new_cat.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@purchase_bp.route('/api/purchaseCategory/delete/<int:c_id>', methods=['DELETE'])
def delete_category(c_id):
    category = PurchaseCategory.query.get_or_404(c_id)
    
    # Check if in use
    if Purchase.query.filter_by(category=category.name).first():
        return jsonify({"status": "error", "message": "Không thể xóa phân loại đang có đơn hàng sử dụng"}), 400

    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({"status": "success", "message": "Đã xóa phân loại"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
