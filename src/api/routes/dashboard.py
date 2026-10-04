from flask import render_template, flash, redirect, request, Response, Blueprint
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, timedelta
from sqlalchemy import func, text, cast, Integer
from src.database.models import *

dashboard_bp = Blueprint('dashboard', __name__)


def get_amount_nearby_month(db_model, today):
    # THIS MONTH
    try:
        date_column = db_model.date_created
    except:
        date_column = db_model.date


    # 1. Đếm số lượng đơn hàng trong tháng
    this_month_count = db_model.query.filter(
        func.extract('month', date_column) == today.month,
        func.extract('year', date_column) == today.year
    ).count()

    # 2. Tính tổng số tiền (Sum)
    # Lưu ý: .scalar() dùng để lấy giá trị số duy nhất từ kết quả trả về
    this_month_amount = db_model.query.with_entities(
        func.sum(db_model.total_amount)
    ).filter(
        func.extract('month', date_column) == today.month,
        func.extract('year', date_column) == today.year
    ).scalar() or 0  # Trả về 0 nếu không có bản ghi nào

    # LAST MONTH

    # 1. Lấy tháng và năm hiện tại
    today = date.today()
    last_month = today.month - 1
    
    # 2. Đếm số lượng đơn hàng trong tháng
    last_month_count = db_model.query.filter(
        func.extract('month', date_column) == last_month,
        func.extract('year', date_column) == today.year,
    ).count()

    # 3. Tính tổng số tiền (Sum)
    # Lưu ý: .scalar() dùng để lấy giá trị số duy nhất từ kết quả trả về
    last_month_amount = db_model.query.with_entities(
        func.sum(db_model.total_amount)
    ).filter(
        func.extract('month', date_column) == last_month,
        func.extract('year', date_column) == today.year
    ).scalar() or 0  # Trả về 0 nếu không có bản ghi nào

    return {
        "this_month_count": this_month_count,
        "this_month_amount": this_month_amount,
        "last_month_count": last_month_count,
        "last_month_amount": last_month_amount
    }

@dashboard_bp.route("/")
def index():

    today = date.today()
    ## QUERY

    # [SALE] ALL
    sale_count = Sale.query.count()

    sale_amount_all = Sale.query.with_entities(
        func.sum(Sale.total_amount)
    ).scalar() or 0

    # [SALE] NEARBY MONTHS
    
    snm = get_amount_nearby_month(Sale, today)
    this_month_sales = snm["this_month_count"]
    this_month_sales_amount = snm["this_month_amount"]
    last_month_sales = snm["last_month_count"]
    last_month_sales_amount = snm["last_month_amount"]
    
    try:
        percentage_sales_amount = last_month_sales_amount / this_month_sales_amount * 100
        percentage_sales = last_month_sales / this_month_sales * 100
    except ZeroDivisionError:
        percentage_sales_amount = 0
        percentage_sales = 0

    # [PURCHASE] ALL
    purchase_count = Purchase.query.count()

    purchase_amount_all = Purchase.query.with_entities(
        func.sum(Purchase.total_amount)
    ).scalar() or 0

    # [PURCHASE] NEARBY MONTHS

    pnm = get_amount_nearby_month(Purchase, today)
    this_month_purchase = pnm["this_month_count"]
    this_month_purchase_amount = pnm["this_month_amount"]
    last_month_purchase = pnm["last_month_count"]
    last_month_purchase_amount = pnm["last_month_amount"]

    try:
        percentage_purchase_amount = last_month_purchase_amount / this_month_purchase_amount * 100
        percentage_purchase = last_month_purchase / this_month_purchase * 100
    except ZeroDivisionError:
        percentage_purchase_amount = 0
        percentage_purchase = 0

    # [CHART] SALE

    return render_template(
        "dashboard.html",
        # Sale
        this_month_sales=this_month_sales,
        this_month_sales_amount=this_month_sales_amount,
        percentage_sales_amount=percentage_sales_amount,
        percentage_sales=percentage_sales,
        # Purchase
        this_month_purchase=this_month_purchase,
        this_month_purchase_amount=this_month_purchase_amount,
        percentage_purchase=percentage_purchase,
        percentage_purchase_amount=percentage_purchase_amount,
        )

@dashboard_bp.route("/api/sale")
def get_sale_data():
    today = datetime.now()

    sales_metric = request.args.get("salesMetric", "").strip()
    sales_period = request.args.get("salesPeriod", "").strip()

    query = db.session.query(Sale)

    # 1. Lọc theo thời gian
    if sales_period == "day":
        query = query.filter(func.extract("day", Sale.date_created) == today.day,
                             func.extract("month", Sale.date_created) == today.month,
                             func.extract("year", Sale.date_created) == today.year)
    elif sales_period == "month":
        query = query.filter(func.extract("month", Sale.date_created) == today.month,
                             func.extract("year", Sale.date_created) == today.year)
    elif sales_period == "year":
        query = query.filter(func.extract("year", Sale.date_created) == today.year)

    labels = []
    values = []
    stats = []

    # 2. Lọc theo bộ lọc (Thời gian, Sản phẩm, Nhân viên)
    # Theo Sản Phẩm
    if sales_metric == "product":
        sales_product_type = request.args.get("salesProductType", "").strip()

        if sales_product_type == "all":
            stats = query.join(SaleItem).join(Product).group_by(Product.id).with_entities(
                Product.name,
                func.sum(SaleItem.quantity)
            ).order_by(func.sum(SaleItem.quantity).desc()).all()
        elif sales_product_type == "cap":
            stats = query.join(SaleItem).join(Product).group_by(Product.cap_type).with_entities(
                Product.cap_type,
                func.sum(SaleItem.quantity)
            ).order_by(func.sum(SaleItem.quantity).desc()).all()
        elif sales_product_type == "bottle":
            stats = query.join(SaleItem).join(Product).group_by(Product.bottle_type).with_entities(
                Product.bottle_type,
                func.sum(SaleItem.quantity)
            ).order_by(func.sum(SaleItem.quantity).desc()).all()
        elif sales_product_type == "capacity":
            stats = query.join(SaleItem).join(Product).group_by(Product.capacity).with_entities(
                Product.capacity,
                func.sum(SaleItem.quantity)
            ).order_by(func.sum(SaleItem.quantity).desc()).all()
    # Theo Nhân viên
    elif sales_metric == "employee":
        stats = query.join(SaleItem).join(Employee).group_by(Employee.id).with_entities(
            Employee.name,
            func.count(Sale.id)
        ).order_by(func.count(Sale.id).desc()).all()
    # Theo Thời gian
    else:
        if sales_period == "hour":
            stats = query.with_entities(
                # SQLite: strftime('%H:00', date, '+7 hours')
                func.strftime("%H:00", Sale.date_created, "+7 hours").label("label"),
                func.count(Sale.id)
            ).group_by(text("label")).order_by(text("label")).all()

        elif sales_period == "day":
            stats = query.with_entities(
                # SQLite: strftime('%Y-%m-%d', date, '+7 hours')
                func.strftime("%d/%m", Sale.date_created, "+7 hours").label("label"),
                func.count(Sale.id)
            ).group_by(text("label")).order_by(text("label")).all()

        elif sales_period == "month":
            stats = query.with_entities(
                # SQLite: strftime('%Y-%m', date, '+7 hours')
                cast(func.strftime("%m", Sale.date_created, "+7 hours"), Integer).label("label"),
                func.count(Sale.id)
            ).group_by(text("label")).order_by(text("label")).all()


        else: #all
            stats = query.with_entities(
                # SQLite: strftime('%Y-%m', date, '+7 hours')
                func.strftime("%Y", Sale.date_created, "+7 hours").label("label"),
                func.count(Sale.id)
            ).group_by(text("label")).order_by(text("label")).all()


    # Kết quả gửi lại cho chart
    labels = [r[0] for r in stats]
    values = [float(r[1] or 0) for r in stats] 

    return {"labels": labels, "data": values}

@dashboard_bp.route("/api/revenue")
def get_revenue_data():
    today = datetime.now()

    revenue_period = request.args.get("revenuePeriod", "").strip()
    revenue_metric = request.args.get("revenueMetric", "").strip()

    query = db.session.query(Sale)

    # 1. Lọc theo thời gian
    if revenue_period == "day":
        query = query.filter(func.extract("day", Sale.date_created) == today.day,
                             func.extract("month", Sale.date_created) == today.month,
                             func.extract("year", Sale.date_created) == today.year)
    elif revenue_period == "month":
        query = query.filter(func.extract("month", Sale.date_created) == today.month,
                             func.extract("year", Sale.date_created) == today.year)
    elif revenue_period == "year":
        query = query.filter(func.extract("year", Sale.date_created) == today.year)

    labels = []
    values = []
    stats = []

    if revenue_metric == 'product':
        stats = query.join(SaleItem).with_entities(
            Product.name,
            func.sum(SaleItem.quantity * SaleItem.price_at_sale)
        ).order_by(func.sum(SaleItem.quantity * SaleItem.price_at_sale).desc()).all()

    else:
        if revenue_period == "day":
            stats = query.join(SaleItem).with_entities(
                # SQLite: strftime('%H:00', date, '+7 hours')
                func.strftime("%d/%m", Sale.date_created, "+7 hours").label("label"),
                func.sum(SaleItem.quantity * SaleItem.price_at_sale)
            ).group_by(text("label")).order_by(text("label")).all()

        elif revenue_period == "quarter":
            # Công thức: (Tháng - 1) / 3 + 1
            # Trong SQLite, ta lấy tháng bằng strftime('%m', ...)
            quarter_num = (func.cast(func.strftime("%m", Sale.date_created, "+7 hours"), db.Integer) - 1) / 3 + 1
    
            stats = query.join(SaleItem).with_entities(
                func.printf("Q%d", quarter_num).label("label"),
                func.sum(SaleItem.quantity * SaleItem.price_at_sale)
            ).group_by(text("label")).order_by(text("label")).all()

        elif revenue_period == "month":
            stats = query.join(SaleItem).with_entities(
                # SQLite: strftime('%Y-%m', date, '+7 hours')
                func.strftime("%m/%Y", Sale.date_created, "+7 hours").label("label"),
                func.sum(SaleItem.quantity * SaleItem.price_at_sale)
            ).group_by(text("label")).order_by(text("label")).all()
        
        elif revenue_period == "year": 
            stats = query.join(SaleItem).with_entities(
                # SQLite: strftime('%Y-%m', date, '+7 hours')
                func.strftime("%Y", Sale.date_created, "+7 hours").label("label"),
                func.sum(SaleItem.quantity * SaleItem.price_at_sale)
            ).group_by(text("label")).order_by(text("label")).all()

    # Kết quả gửi lại cho chart
    labels = [r[0] for r in stats]
    values = [float(r[1] or 0) for r in stats] 

    return {"labels": labels, "data": values}  

@dashboard_bp.route('/api/expense')
def get_expense_data():
    today = datetime.now()

    query = db.session.query(Purchase)

    expense_period = request.args.get("expensePeriod", "").strip()

    labels = []
    values = []
    stats = []

    # 1. Lọc theo thời gian
    if expense_period == "day":
        query = query.filter(func.extract("day", Purchase.date) == today.day,
                             func.extract("month", Purchase.date) == today.month,
                             func.extract("year", Purchase.date) == today.year)

        stats = query.with_entities(
            func.strftime("%H:00", Purchase.date, "+7 hours").label("label"),
            func.sum(Purchase.total_amount)
        ).group_by(text("label")).order_by(text("label")).all()
            
    elif expense_period == "month":
        query = query.filter(func.extract("month", Purchase.date) == today.month,
                             func.extract("year", Purchase.date) == today.year)

        stats = query.with_entities(
            func.strftime("%d/%m", Purchase.date, "+7 hours").label("label"),
            func.sum(Purchase.total_amount)
        ).group_by(text("label")).order_by(text("label")).all()

    elif expense_period == "year":
        query = query.filter(func.extract("year", Purchase.date) == today.year)

        stats = query.with_entities(
            func.strftime("%m/%Y", Purchase.date, "+7 hours").label("label"),
            func.sum(Purchase.total_amount)
        ).group_by(text("label")).order_by(text("label")).all()
    else:
        stats = query.with_entities(
            func.strftime("%Y", Purchase.date, "+7 hours").label("label"),
            func.sum(Purchase.total_amount)
        ).group_by(text("label")).order_by(text("label")).all()


    labels = [r[0] for r in stats]
    values = [float(r[1] or 0) for r in stats]

    return {"labels": labels, "data": values}

