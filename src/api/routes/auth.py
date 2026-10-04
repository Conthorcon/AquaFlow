from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from src.database.models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return jsonify({"status": "error", "message": "Quyền truy cập bị từ chối"}), 403
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            if user.role == 'admin':
                return redirect(url_for('auth.admin_accounts'))
            return redirect(url_for('dashboard.index'))
        
        flash('Tên đăng nhập hoặc mật khẩu không chính xác', 'error')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/admin/accounts')
@login_required
def admin_accounts():
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard.index'))
    users = User.query.filter(User.role != 'admin').all()
    return render_template('admin_accounts.html', users=users)

# API Management
@auth_bp.route('/api/admin/users')
@login_required
@admin_required
def list_users():
    users = User.query.filter(User.role != 'admin').all()
    return jsonify([{"id": u.id, "username": u.username, "role": u.role} for u in users])

@auth_bp.route('/api/admin/user/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if User.query.filter_by(username=username).first():
        return jsonify({"status": "error", "message": "Tên đăng nhập đã tồn tại"}), 400
        
    new_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role='staff'
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"status": "success", "message": "Tạo tài khoản thành công"})

@auth_bp.route('/api/admin/user/delete/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        return jsonify({"status": "error", "message": "Không thể xóa tài khoản Admin"}), 400
        
    db.session.delete(user)
    db.session.commit()
    return jsonify({"status": "success", "message": "Đã xóa tài khoản"})
