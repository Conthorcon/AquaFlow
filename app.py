import os
import secrets
import click
from sqlalchemy.pool import NullPool
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

# Vercel requires an external database: local files are not persistent.
# Local development keeps SQLite unless DATABASE_URL is supplied.
on_vercel = os.environ.get("VERCEL") == "1"
database_url = os.environ.get("DATABASE_URL", "sqlite:///aquasupply.db")
for prefix in ("postgres://", "postgresql://"):
    if database_url.startswith(prefix):
        database_url = "postgresql+psycopg://" + database_url[len(prefix):]
        break
if on_vercel and not database_url.startswith("postgresql+psycopg://"):
    raise RuntimeError("Vercel requires a PostgreSQL DATABASE_URL")
if on_vercel and not os.environ.get("SECRET_KEY"):
    raise RuntimeError("Set SECRET_KEY in Vercel Environment Variables")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Set a stable SECRET_KEY to preserve local sessions across restarts.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
if database_url.startswith("postgresql"):
    # Avoid a pool per serverless instance; use the database provider pooled URL.
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": NullPool}
if on_vercel:
    app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE="Lax")

db.init_app(app)


@app.cli.command("init-db")
def init_db():
    """Create missing tables once; do not delete or migrate existing data."""
    db.create_all()
    click.echo("Database tables initialized.")


@app.cli.command("create-admin")
@click.option("--username", prompt=True)
@click.password_option()
def create_admin(username, password):
    """Create an admin explicitly; never seed default credentials at startup."""
    if not username.strip() or len(password) < 12:
        raise click.ClickException("Username is required; password must have at least 12 characters.")
    if User.query.filter_by(username=username).first():
        raise click.ClickException("Username already exists; no account was changed.")
    db.session.add(User(username=username, password_hash=generate_password_hash(password), role="admin"))
    db.session.commit()
    click.echo("Admin created.")


# Authentication Protection
@app.before_request
def check_login():
    # List of endpoints that don't require login
    allowed_endpoints = ['auth.login', 'static', 'sale.add_zalo_order', 'sale.confirm_zalo_order']
    if request.endpoint not in allowed_endpoints and 'user_id' not in session:
        return redirect(url_for('auth.login'))

if __name__ == "__main__":
    app.run(debug=True, port=4849)
