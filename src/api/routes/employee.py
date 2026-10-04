from flask import Blueprint, render_template, request, jsonify
from src.database.models import db, Employee
import json

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/employee')
def index():
    # We no longer need EmployeeRole database seeding
    employees = Employee.query.all()
    # We can pass a fixed list of roles for the UI dropdown, but keep them as strings in the DB
    roles = ["Quản lý", "Kế toán", "Giao hàng", "Kỹ thuật", "Khác"]
    return render_template('employee.html', roles=roles, employees=employees)

@employee_bp.route('/api/employeeList')
def get_employee_list():
    q = request.args.get('q', '')
    query = Employee.query
    if q:
        query = query.filter(
            (Employee.name.contains(q)) | 
            (Employee.role.contains(q))
        )
    employees = query.all()
    
    result = []
    for e in employees:
        result.append({
            "id": e.id,
            "name": e.name,
            "role": e.role
        })
    return jsonify(result)

@employee_bp.route('/api/employee/add', methods=['POST'])
def add_employee():
    data = request.get_json()
    try:
        new_emp = Employee(
            name=data.get('name'),
            role=data.get('role')
        )
        db.session.add(new_emp)
        db.session.commit()
        return jsonify({"status": "success", "message": "Thêm nhân viên thành công", "id": new_emp.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@employee_bp.route('/api/employee/update', methods=['POST'])
def update_employee():
    data = request.get_json()
    e_id = data.get('id')
    if not e_id:
        return jsonify({"status": "error", "message": "Thiếu mã nhân viên"}), 400
        
    employee = Employee.query.get_or_404(e_id)
    try:
        employee.name = data.get('name')
        employee.role = data.get('role')
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Cập nhật nhân viên thành công"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@employee_bp.route('/api/employee/delete/<int:e_id>', methods=['DELETE'])
def delete_employee(e_id):
    employee = Employee.query.get_or_404(e_id)
    try:
        db.session.delete(employee)
        db.session.commit()
        return jsonify({"status": "success", "message": "Đã xóa nhân viên"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
