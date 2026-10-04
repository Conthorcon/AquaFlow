from flask import Flask, render_template, url_for, flash, redirect, request, Response, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func, text
from src.database.models import *
from werkzeug.security import generate_password_hash

from src.api.routes.dashboard import dashboard_bp
from src.api.routes.sale import sale_bp
from src.api.routes.customer import customer_bp
from src.api.routes.inventory import inventory_bp
from src.api.routes.purchase import purchase_bp
from src.api.routes.employee import employee_bp
from src.api.routes.auth import auth_bp
from src.api.routes.sale_import import sale_import_bp
from src.api.routes.chatbot import chatbot_bp

CAPS = ["Nắp xanh", "Nắp đỏ", "Bình bằng"]

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")

# Register Blueprints
app.register_blueprint(dashboard_bp)
app.register_blueprint(sale_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(purchase_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(sale_import_bp)
app.register_blueprint(chatbot_bp)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///aquasupply.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "aqua-flow-secret-key-2024"

# Liên kết SQLAlchemy với App
db.init_app(app)

# Khởi tạo db và seed admin
with app.app_context():
    db.create_all()
    # Seed default admin
    if not User.query.filter_by(role='admin').first():
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('admin@123'),
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()

# Authentication Protection
@app.before_request
def check_login():
    # List of endpoints that don't require login
    allowed_endpoints = ['auth.login', 'static', 'sale.add_zalo_order', 'sale.confirm_zalo_order']
    if request.endpoint not in allowed_endpoints and 'user_id' not in session:
        return redirect(url_for('auth.login'))

if __name__ == "__main__":
    app.run(debug=True, port=4849)