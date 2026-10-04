from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# --- PHẢI CẤU HÌNH VÀ KHỞI TẠO DB TRƯỚC KHI ĐỊNH NGHĨA MODEL ---
db = SQLAlchemy()

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    deliveries = db.relationship('Sale', back_populates='delivery_person', foreign_keys="Sale.delivery_employee_id")

class CustomerGroup(db.Model):
    """Phân loại nhóm khách hàng: Sỉ, Lẻ, Công ty, Đại lý..."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True) # Ví dụ: 'Wholesale', 'Retail'
    customers = db.relationship('Customer', backref='group', lazy=True)
    prices = db.relationship('ProductPriceConfig', backref='group', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cap_type = db.Column(db.String(50), nullable=False)
    bottle_type = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.String(50), nullable=False)
    # Không để giá ở đây nữa hoặc để giá niêm yết mặc định
    # base_price = db.Column(db.Float, default=0.0) # Đã xóa - sử dụng group price 
    
    price_configs = db.relationship('ProductPriceConfig', backref='product', lazy=True)
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)

class ProductPriceConfig(db.Model):
    """Bảng trung gian định nghĩa giá cho từng sản phẩm theo từng loại khách"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('customer_group.id'), nullable=False)
    price = db.Column(db.Float, nullable=False) # Giá áp dụng cho nhóm này

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    group_id = db.Column(db.Integer, db.ForeignKey('customer_group.id'), nullable=False)
    sales = db.relationship('Sale', backref='customer', lazy=True)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    delivery_employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))   
     
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    date_delivery = db.Column(db.DateTime, nullable=True)
    date_completed = db.Column(db.DateTime, nullable=True)
    tax = db.Column(db.Float, nullable=False, default=0.0)
    note = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(50), default="pending")
    
    sale_items = db.relationship('SaleItem', backref='sale', lazy=True)
    delivery_person = db.relationship('Employee', back_populates='deliveries', foreign_keys=[delivery_employee_id])

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_sale = db.Column(db.Float, nullable=False) # Quan trọng: Lưu giá lúc bán

class PurchaseCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)

class Inventory(db.Model):
    """Theo dõi số lượng tồn kho cho từng sản phẩm"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, unique=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    note = db.Column(db.String(200), nullable=True)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    product = db.relationship('Product', backref=db.backref('inventory', uselist=False))

class User(db.Model):
    """Quản lý tài khoản đăng nhập"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff') # 'admin' or 'staff'

class ZaloOrder(db.Model):
    """Lưu trữ đơn hàng từ Zalo đợi quản lý xác nhận duyệt"""
    id = db.Column(db.Integer, primary_key=True)
    zalo_user_id = db.Column(db.String(50), nullable=False)
    order_data = db.Column(db.Text, nullable=False) # JSON chứa productList ["products": ...]
    status = db.Column(db.String(20), default="pending_manager") 
    created_at = db.Column(db.DateTime, default=datetime.now)
