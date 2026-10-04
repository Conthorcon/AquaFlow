from flask import render_template, flash, redirect, request, Response, Blueprint, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, timedelta
from sqlalchemy import func, text
from src.database.models import *
from utils.import_logic import fuzzy_match, get_product_choices

sale_bp = Blueprint('sale', __name__)

@sale_bp.route('/sale')
def sale():
    today = date.today()
    
    # 0. Lấy thông số lọc
    filter_mode = request.args.get('mode', 'default')
    f_day = request.args.get('day')
    f_month = request.args.get('month')
    f_year = request.args.get('year')

    # Convert to int if provided, else None
    try:
        f_day = int(f_day) if f_day else None
        f_month = int(f_month) if f_month else None
        f_year = int(f_year) if f_year else None
    except ValueError:
        f_day = f_month = f_year = None

    # Base query
    query = db.session.query(
        Sale.id,
        Customer.name.label('customer_name'),
        Customer.phone.label('customer_phone'),
        Customer.address.label('customer_address'),
        func.strftime("%d/%m/%Y %H:%M", Sale.date_created, "+7 hours").label('date_created'),
        func.strftime("%d/%m/%Y %H:%M", Sale.date_delivery, "+7 hours").label('date_delivery'),
        func.strftime("%d/%m/%Y %H:%M", Sale.date_completed, "+7 hours").label('date_completed'),
        Product.name.label('product_name'),
        SaleItem.quantity,
        SaleItem.price_at_sale,
        Sale.status,
        Sale.tax,
        Sale.note,
        Employee.name.label('delivery_name'),
        Sale.delivery_employee_id,
        Sale.date_created.label('raw_date_created'),
        Sale.date_completed.label('raw_date_completed')
    ).select_from(Sale) \
    .join(Customer, Sale.customer_id == Customer.id) \
    .join(SaleItem, Sale.id == SaleItem.sale_id) \
    .join(Product, SaleItem.product_id == Product.id) \
    .outerjoin(Employee, Sale.delivery_employee_id == Employee.id)

    # Apply filters
    if filter_mode == 'time':
        # Default empty to current date
        target_day = f_day if f_day is not None else today.day
        target_month = f_month if f_month is not None else today.month
        target_year = f_year if f_year is not None else today.year
        target_date_str = f"{target_year:04d}-{target_month:02d}-{target_day:02d}"
        
        query = query.filter(func.date(Sale.date_created) == target_date_str)
    else:
        # Default mode:
        # - pending/delivering: không lọc ngày
        # - completed: chỉ hiện trong ngày
        today_str = today.strftime('%Y-%m-%d')
        query = query.filter(
            (Sale.status.in_(['pending', 'delivering'])) |
            (
                (Sale.status == 'completed') &
                (func.date(Sale.date_completed) == today_str)
            )
        )


    q_all_sales = query.all()

    # 2. Gom nhóm dữ liệu
    sales_map = {}

    for row in q_all_sales:
        sale_id = row.id
        if sale_id not in sales_map:
            sales_map[sale_id] = {
                "id": sale_id,
                "customer_name": row.customer_name,
                "customer_phone": row.customer_phone if row.customer_phone else "-",
                "customer_address": row.customer_address if row.customer_address else "-",
                "date_created": row.date_created,
                "date_delivery": row.date_delivery if row.date_delivery else "-",
                "date_completed": row.date_completed if row.date_completed else "-",
                "status": row.status,
                "tax": row.tax,
                "note": row.note if row.note else "",
                "delivery_name": row.delivery_name if row.delivery_name else "Chưa gán",
                "delivery_employee_id": row.delivery_employee_id,
                "price_at_sale": 0,
                "products": []
            }
        
        sales_map[sale_id]["products"].append({
            "name": row.product_name,
            "quantity": row.quantity
        })
        sales_map[sale_id]["price_at_sale"] += (row.price_at_sale * row.quantity)

    # 3. Chia danh sách theo trạng thái
    pending_sales = [s for s in sales_map.values() if s["status"] == "pending"]
    delivering_sales = [s for s in sales_map.values() if s["status"] == "delivering"]
    completed_sales = [s for s in sales_map.values() if s["status"] == "completed"]

    # Thống kê (lấy từ dữ liệu đã lọc hoặc query riêng?)
    # Thống kê nên lấy theo ngày hôm nay bất kể mode lọc
    # today_str = today.strftime('%Y-%m-%d')
    # today_sales_count = Sale.query.filter(func.date(Sale.date_created) == today_str).count()

    # today_delivering_count = Sale.query.filter(
    #     func.date(Sale.date_created) == today_str,
    #     Sale.status == "delivering"
    # ).count()

    # today_pending_count = Sale.query.filter(
    #     func.date(Sale.date_created) == today_str,
    #     Sale.status == "pending"
    # ).count()

    today_sales_count = len(pending_sales) + len(delivering_sales) + len(completed_sales)
    today_delivering_count = len(delivering_sales)
    today_pending_count = len(pending_sales)
    

    # Lấy danh sách nhân viên để chọn
    employees = Employee.query.all()

    # Zalo Orders
    zalo_orders = ZaloOrder.query.filter_by(status='pending_manager').order_by(ZaloOrder.created_at.desc()).all()
    import json
    for zo in zalo_orders:
        try:
            zo.parsed = json.loads(zo.order_data)
        except Exception:
            zo.parsed = {"products": []}

    return render_template("sale.html",
                            zalo_orders=zalo_orders,
                            pending_sales=pending_sales,
                            delivering_sales=delivering_sales,
                            completed_sales=completed_sales,
                            employees=employees,
                            today_sales=today_sales_count,
                            today_delivering_sales=today_delivering_count,
                            today_pending_sales=today_pending_count,
                            filter_mode=filter_mode,
                            f_day=f_day,
                            f_month=f_month,
                            f_year=f_year)


@sale_bp.route("/api/sale/update_status", methods=['POST'])
def update_status():
    data = request.get_json()
    sale_id = data.get('id')
    new_status = data.get('status')
    sale = Sale.query.get(sale_id)
    if sale:
        sale.status = new_status
        if new_status == 'completed':
            sale.date_completed = datetime.now()
        if new_status == 'delivering':
            sale.date_delivery = datetime.now()
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Không tìm thấy đơn hàng"}), 404

@sale_bp.route("/api/sale/assign_delivery", methods=['POST'])
def assign_delivery():
    data = request.get_json()
    sale_id = data.get('id')
    employee_id = data.get('employee_id')
    sale = Sale.query.get(sale_id)

    if sale:
        sale.delivery_employee_id = employee_id
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Không tìm thấy đơn hàng"}), 404

@sale_bp.route("/api/customerList")
def get_customer_list():
    customers = Customer.query.all()
    customer_list = [{
        "id": c.id,
        "name": c.name,
        "phone": c.phone if c.phone else "",
        "address": c.address if c.address else "",
        "group_id": c.group_id
    } for c in customers]

    return jsonify(customer_list)
    

@sale_bp.route("/api/productList")
def get_product_list():
    products = Product.query.all()
    product_list = []
    for p in products:
        configs = ProductPriceConfig.query.filter_by(product_id=p.id).all()
        prices = {str(c.group_id): c.price for c in configs}
        product_list.append({
            "id": p.id,
            "name": p.name,
            "prices": prices,
            "bottle_type": p.bottle_type,
            "cap_type": p.cap_type,
            "capacity": p.capacity,
        })

    return jsonify(product_list)

@sale_bp.route("/api/addSales", methods=['POST'])
def add_order():
    data = request.get_json()

    total_amount = data.get('totalAmount')
    tax = data.get('tax')
    customer_name = data.get('customerName')
    customer_phone = data.get('customerPhone')
    customer_address = data.get('customerAddress')
    product_list = data.get('productList')
    note = data.get('note')

    # 1. Xử lý khách hàng
    customer = Customer.query.filter_by(name=customer_name).first()
    if not customer:
        # Tạo mới khách hàng nếu chưa có
        customer = Customer(
            name=customer_name, 
            phone=customer_phone, 
            address=customer_address, 
            group_id=1 # Mặc định là nhóm khách lẻ
        )
        db.session.add(customer)
        db.session.flush()
    else:
        # Cập nhật thông tin nếu trong DB còn thiếu
        if customer_phone and not customer.phone:
            customer.phone = customer_phone
        if customer_address and not customer.address:
            customer.address = customer_address

    # 2. Tạo đơn bán hàng
    sale = Sale(
        tax=tax,
        customer_id=customer.id,
        date_created=datetime.now(),
        note=note,
        )

    db.session.add(sale)
    db.session.flush()

    for p in product_list:
        # Lấy product object
        product_obj = Product.query.filter_by(name=p["name"]).first()
        if product_obj:
            saleItem = SaleItem(
                sale_id=sale.id,
                product_id=product_obj.id,
                quantity=p["quantity"],
                price_at_sale=p["price"] # Lấy giá cụ thể của từng item từ frontend
            )
            db.session.add(saleItem)

            # Trừ tồn kho (nếu có) - không block đơn khi hết hàng
            inv = Inventory.query.filter_by(product_id=product_obj.id).first()
            if inv and inv.quantity > 0:
                inv.quantity = max(0, inv.quantity - int(p["quantity"]))
                inv.last_updated = datetime.now()

    try:
        db.session.commit()
        return jsonify({"status": "success", "redirect_url": url_for("sale.sale")}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@sale_bp.route("/api/zalo_order/add", methods=['POST'])
def add_zalo_order():
    data = request.get_json()
    zalo_user_id = data.get('zalo_user_id')
    order_data = data.get('order_data')
    import json
    zo = ZaloOrder(zalo_user_id=zalo_user_id, order_data=json.dumps(order_data))
    db.session.add(zo)
    db.session.commit()
    return jsonify({"status": "success"})

@sale_bp.route("/api/zalo_order/approve", methods=['POST'])
def approve_zalo_order():
    data = request.get_json()
    order_id = data.get('id')
    zo = ZaloOrder.query.get(order_id)
    if zo and zo.status == 'pending_manager':
        zo.status = 'pending_customer'
        db.session.commit()
        # Ping Zalo user
        import requests
        import json
        BOT_TOKEN = "3431117687435998990:oVWhauqbbdMqVhGpaGoFdxjZvckbQVPuJPqzUJUGSqEQDLsqQEidVsxdXyVryVTm"
        URL = f"https://bot-api.zaloplatforms.com/bot{BOT_TOKEN}"
        
        try:
            parsed = json.loads(zo.order_data)
            products = parsed.get("products", [])
            details = []
            for p in products:
                details.append(f'- {p.get("quantity", 1)} x {p.get("name", "")}')
            confirm_msg = "Cửa hàng đã xem và lên đơn:\n" + "\n".join(details) + "\n\nVui lòng nhắn 'xác nhận' để chốt đơn."
            
            requests.post(f"{URL}/sendMessage", json={"chat_id": zo.zalo_user_id, "text": confirm_msg}, headers={"Content-Type": "application/json"})
        except Exception as e:
            print("Lỗi Zalo message", e)

        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@sale_bp.route("/api/zalo_order/confirm", methods=['POST'])
def confirm_zalo_order():
    data = request.get_json()
    zalo_user_id = data.get('zalo_user_id')
    user_name = data.get('user_name')
    import json
    zo = ZaloOrder.query.filter_by(zalo_user_id=zalo_user_id, status='pending_customer').order_by(ZaloOrder.id.desc()).first()
    if not zo:
        return jsonify({"status": "not_found"})
    try:
        order_data = json.loads(zo.order_data)
    except:
        order_data = {"products": []}
        
    customer = Customer.query.filter_by(name=user_name).first()
    if not customer:
        customer = Customer(name=user_name, phone="", group_id=1)
        db.session.add(customer)
        db.session.flush()
        
    sale = Sale(
        customer_id=customer.id,
        date_created=datetime.now(),
        note="Đơn Zalo tự động"
    )
    db.session.add(sale)
    db.session.flush()

    def normalize(text):
        return text.lower().strip()

    products = order_data.get("products", [])


    product_choices = Product.query.all()

    product_choices = {p.name: p.id for p in product_choices}

    for p in products:
        product_obj = fuzzy_match(p.get("name"), product_choices, threshold=0.5)
        print(product_obj)
        if product_obj:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product_obj,
                quantity=p.get("quantity", 1),
                price_at_sale=0
            )
            db.session.add(sale_item)
        else:
            return jsonify({
                "status": "error",
                "message": f"Không tìm thấy sản phẩm gần đúng với '{p.get('name')}'"
            })

    zo.status = 'completed'
    db.session.commit()
    return jsonify({"status": "success"})

@sale_bp.route('/sale/view/<int:id>')
def view(id):
    sale = Sale.query.get_or_404(id)
    return render_template('edit_sale.html', id=id, mode='view')

@sale_bp.route('/sale/edit/<int:id>')
def edit(id):
    sale = Sale.query.get_or_404(id)
    employees = Employee.query.all()
    return render_template('edit_sale.html', id=id, mode='edit', employees=employees)

@sale_bp.route('/api/sale/<int:id>')
def get_sale_detail(id):
    sale = Sale.query.get_or_404(id)
    
    # Pre-calculated items
    items = []
    for item in sale.sale_items:
        items.append({
            "product_id": item.product_id,
            "product_name": item.product.name,
            "quantity": item.quantity,
            "price_at_sale": item.price_at_sale
        })
    
    sale_data = {
        "id": sale.id,
        "customer_id": sale.customer_id,
        "customer_group_id": sale.customer.group_id,
        "customer_name": sale.customer.name,
        "customer_phone": sale.customer.phone,
        "customer_address": sale.customer.address,
        "status": sale.status,
        "tax": sale.tax,
        "note": sale.note,
        "delivery_employee_id": sale.delivery_employee_id,
        "date_created": sale.date_created.strftime("%d/%m/%Y %H:%M") if sale.date_created else "-",
        "date_delivery": sale.date_delivery.strftime("%d/%m/%Y %H:%M") if sale.date_delivery else "-",
        "date_completed": sale.date_completed.strftime("%d/%m/%Y %H:%M") if sale.date_completed else "-",
        "items": items
    }
    return jsonify(sale_data)

@sale_bp.route('/api/sale/update', methods=['POST'])
def update_sale():
    data = request.get_json()
    sale_id = data.get('id')
    sale = Sale.query.get(sale_id)
    
    if not sale:
        return jsonify({"status": "error", "message": "Không tìm thấy đơn hàng"}), 404
    
    if sale.status == 'completed':
         return jsonify({"status": "error", "message": "Không thể chỉnh sửa đơn hàng đã hoàn thành"}), 403

    # Update basic fields
    sale.tax = data.get('tax', sale.tax)
    sale.note = data.get('note', sale.note)
    sale.status = data.get('status', sale.status)
    sale.delivery_employee_id = data.get('delivery_employee_id', sale.delivery_employee_id)
    
    if sale.status == 'completed' and not sale.date_completed:
        sale.date_completed = datetime.now()
    if sale.status == 'delivering' and not sale.date_delivering:
        sale.date_delivering = datetime.now()

    # Update items: Clear and Re-add (Simplest way)
    SaleItem.query.filter_by(sale_id=sale.id).delete()
    
    total_amount = 0
    product_list = data.get('productList', [])
    for p in product_list:
        product_obj = Product.query.filter_by(name=p["name"]).first()
        if product_obj:
            item_price = float(p["price"])
            item_qty = int(p["quantity"])
            saleItem = SaleItem(
                sale_id=sale.id,
                product_id=product_obj.id,
                quantity=item_qty,
                price_at_sale=item_price
            )
            db.session.add(saleItem)
            total_amount += (item_price * item_qty)
    
    sale.total_amount = total_amount
    
    try:
        db.session.commit()
        return jsonify({"status": "success", "message": "Cập nhật thành công"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@sale_bp.route('/api/sale/<int:id>', methods=['DELETE'])
def delete_sale(id):
    sale = Sale.query.get_or_404(id)
    try:
        # Xóa các SaleItem trước để tránh vi phạm foreign key
        SaleItem.query.filter_by(sale_id=sale.id).delete()
        db.session.delete(sale)
        db.session.commit()
        return jsonify({"status": "success", "message": "Đã xóa đơn hàng"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500