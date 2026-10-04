from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from src.database.models import *

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/inventory')
def inventory():
    """Trang danh sách tồn kho"""
    products = Product.query.all()
    groups = CustomerGroup.query.all()

    inventory_data = []
    for p in products:
        inv = p.inventory
        prices_by_group = {}
        for cfg in p.price_configs:
            if cfg.price and cfg.price > 0:
                prices_by_group[cfg.group_id] = cfg.price

        inventory_data.append({
            "product_id": p.id,
            "product_name": p.name,
            "cap_type": p.cap_type,
            "bottle_type": p.bottle_type,
            "capacity": p.capacity,
            "prices_by_group": prices_by_group,
            "quantity": inv.quantity if inv else 0,
            "note": inv.note if inv else "",
            "last_updated": inv.last_updated.strftime("%d/%m/%Y %H:%M") if inv else "Chưa cập nhật"
        })

    # Truyền groups dưới dạng list of dict để JS dùng
    groups_data = [{"id": g.id, "name": g.name} for g in groups]

    return render_template("inventory.html",
                           inventory_data=inventory_data,
                           groups=groups,
                           groups_json=groups_data)


@inventory_bp.route('/api/inventory', methods=['GET'])
def get_inventory():
    """API: Lấy danh sách tồn kho"""
    products = Product.query.all()
    result = []
    for p in products:
        inv = p.inventory
        result.append({
            "product_id": p.id,
            "product_name": p.name,
            "quantity": inv.quantity if inv else 0,
        })
    return jsonify(result)


@inventory_bp.route('/api/inventory/update', methods=['POST'])
def update_inventory():
    """API: Cập nhật số lượng tồn kho"""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    mode = data.get('mode', 'set')
    note = data.get('note', '')

    if product_id is None or quantity is None:
        return jsonify({"status": "error", "message": "Thiếu thông tin"}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"status": "error", "message": "Không tìm thấy sản phẩm"}), 404

    inv = Inventory.query.filter_by(product_id=product_id).first()
    if not inv:
        inv = Inventory(product_id=product_id, quantity=0)
        db.session.add(inv)

    if mode == 'add':
        inv.quantity = max(0, inv.quantity + int(quantity))
    else:
        inv.quantity = max(0, int(quantity))

    if note:
        inv.note = note
    inv.last_updated = datetime.now()

    try:
        db.session.commit()
        return jsonify({"status": "success", "quantity": inv.quantity})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@inventory_bp.route('/api/inventory/update_price_single', methods=['POST'])
def update_price_single():
    """API: Cập nhật giá cho một cặp (product, group) cụ thể"""
    data = request.get_json()
    product_id = data.get('product_id')
    group_id = int(data.get('group_id'))
    price = float(data.get('price', 0))

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"status": "error", "message": "Không tìm thấy sản phẩm"}), 404

    cfg = ProductPriceConfig.query.filter_by(
        product_id=product_id, group_id=group_id
    ).first()
    if cfg:
        cfg.price = price
    else:
        db.session.add(ProductPriceConfig(
            product_id=product_id, group_id=group_id, price=price
        ))

    try:
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@inventory_bp.route('/api/inventory/update_prices', methods=['POST'])
def update_prices():
    """API: Cập nhật giá nhiều nhóm cùng lúc cho một sản phẩm"""
    data = request.get_json()
    product_id = data.get('product_id')
    group_prices = data.get('group_prices', {})

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"status": "error", "message": "Không tìm thấy sản phẩm"}), 404

    for group_id_str, price in group_prices.items():
        group_id = int(group_id_str)
        cfg = ProductPriceConfig.query.filter_by(
            product_id=product_id, group_id=group_id
        ).first()
        if cfg:
            cfg.price = float(price)
        else:
            db.session.add(ProductPriceConfig(
                product_id=product_id, group_id=group_id, price=float(price)
            ))

    try:
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@inventory_bp.route('/api/inventory/add_product', methods=['POST'])
def add_product():
    """API: Thêm sản phẩm mới kèm tồn kho và giá theo nhóm"""
    data = request.get_json()
    name = data.get('name', '').strip()
    cap_type = data.get('cap_type', '').strip()
    bottle_type = data.get('bottle_type', '').strip()
    capacity = data.get('capacity', '').strip()
    initial_qty = int(data.get('initial_qty', 0))
    group_prices = data.get('group_prices', {})

    if not name:
        return jsonify({"status": "error", "message": "Tên sản phẩm không được để trống"}), 400

    existing = Product.query.filter_by(name=name).first()
    if existing:
        return jsonify({"status": "error", "message": "Sản phẩm với tên này đã tồn tại"}), 400

    product = Product(
        name=name,
        cap_type=cap_type,
        bottle_type=bottle_type,
        capacity=capacity,
        # base_price=0  # giữ trường nhưng không dùng trong UI
    )
    db.session.add(product)
    db.session.flush()

    for group_id_str, price in group_prices.items():
        if price is not None and float(price) > 0:
            db.session.add(ProductPriceConfig(
                product_id=product.id,
                group_id=int(group_id_str),
                price=float(price)
            ))

    db.session.add(Inventory(product_id=product.id, quantity=initial_qty))

    try:
        db.session.commit()
        return jsonify({"status": "success", "product_id": product.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
