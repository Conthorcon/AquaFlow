from flask import render_template, flash, redirect, request, Response, Blueprint, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, timedelta
from sqlalchemy import func, text
from src.database.models import *

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/customer')
def customer_page():
    # Lấy danh sách nhóm khách hàng
    groups = CustomerGroup.query.all()
    groups_json = [{"id": g.id, "name": g.name} for g in groups]
    
    # Lấy danh sách khách hàng ban đầu (có thể load qua JS sau)
    customers = Customer.query.all()
    
    return render_template('customer.html', groups_json=groups_json, customers=customers)

@customer_bp.route('/api/customers')
def get_customers():
    customers = Customer.query.all()
    results = []
    for c in customers:
        results.append({
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "address": c.address,
            "group_id": c.group_id,
            "group_name": c.group.name if c.group else "Không xác định"
        })
    return jsonify(results)
@customer_bp.route('/api/addCustomer', methods=['POST'])
def addCustomer():
    # Hỗ trợ cả JSON và Form-data
    if request.is_json:
        data = request.json
        name = data.get('name')
        phone = data.get('phone')
        street = data.get('street', '')
        ward = data.get('ward', '')
        city = data.get('city', '')
        group_id = data.get('group_id')
        
        # Ghép địa chỉ
        address_parts = [p for p in [street, ward, city] if p]
        address = ", ".join(address_parts)
    else:
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        group_id = request.form.get('group_id')

    if not name or not group_id:
        return jsonify({'message': 'Thiếu thông tin bắt buộc'}), 400

    # Kiểm tra xem tên đã tồn tại chưa
    existing_customer = Customer.query.filter_by(name=name, phone=phone).first()
    if existing_customer:
        return jsonify({'message': 'Khách hàng này đã tồn tại!'}), 400

    customer = Customer(name=name, phone=phone, address=address, group_id=group_id)
    
    try:
        db.session.add(customer)
        db.session.commit()
        return jsonify({'message': 'Thêm khách hàng thành công', 'id': customer.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Có lỗi xảy ra khi lưu dữ liệu', 'error': str(e)}), 500

@customer_bp.route('/api/updateCustomer', methods=['POST'])
def updateCustomer():
    data = request.json
    customer_id = data.get('id')
    name = data.get('name')
    phone = data.get('phone')
    street = data.get('street', '')
    ward = data.get('ward', '')
    city = data.get('city', '')
    group_id = data.get('group_id')

    if not customer_id or not name or not group_id:
        return jsonify({'message': 'Thiếu thông tin bắt buộc'}), 400

    customer = Customer.query.get_or_404(customer_id)
    
    # Ghép địa chỉ
    address_parts = [p for p in [street, ward, city] if p]
    address = ", ".join(address_parts)

    customer.name = name
    customer.phone = phone
    customer.address = address
    customer.group_id = group_id

    try:
        db.session.commit()
        return jsonify({'message': 'Cập nhật thông tin thành công'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Lỗi khi cập nhật dữ liệu', 'error': str(e)}), 500

@customer_bp.route('/api/deleteCustomer/<int:customer_id>', methods=['DELETE'])
def deleteCustomer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    try:
        db.session.delete(customer)
        db.session.commit()
        return jsonify({'message': 'Xóa khách hàng thành công'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Không thể xóa khách hàng', 'error': str(e)}), 500

@customer_bp.route('/api/addGroup', methods=['POST'])
def addGroup():
    data = request.json
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'message': 'Tên nhóm không được để trống'}), 400
        
    existing = CustomerGroup.query.filter_by(name=name).first()
    if existing:
        return jsonify({'message': 'Nhóm này đã tồn tại'}), 400
        
    group = CustomerGroup(name=name)
    try:
        db.session.add(group)
        db.session.commit()
        return jsonify({'message': 'Thêm nhóm thành công', 'id': group.id, 'name': group.name}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Có lỗi xảy ra', 'error': str(e)}), 500

@customer_bp.route('/api/deleteGroup/<int:group_id>', methods=['DELETE'])
def deleteGroup(group_id):
    group = CustomerGroup.query.get_or_404(group_id)
    
    # Kiểm tra xem có khách hàng nào thuộc nhóm này không
    customer_count = Customer.query.filter_by(group_id=group_id).count()
    if customer_count > 0:
        return jsonify({'message': f'Không thể xóa nhóm này vì đang có {customer_count} khách hàng thuộc nhóm.'}), 400
        
    try:
        db.session.delete(group)
        db.session.commit()
        return jsonify({'message': 'Xóa nhóm khách hàng thành công'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Có lỗi xảy ra', 'error': str(e)}), 500

    