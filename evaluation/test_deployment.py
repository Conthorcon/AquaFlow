"""Deployment checks against an isolated database; never touches instance/aquasupply.db."""
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-only"
os.environ.pop("VERCEL", None)
import unittest
from datetime import datetime
from sqlalchemy import inspect, select
from sqlalchemy.dialects import postgresql
from app import app, db
from src.database.models import Sale, SaleItem, Customer, CustomerGroup, Product, Purchase
from src.database.date_sql import display_date

class DeploymentTests(unittest.TestCase):
    def test_deployment(self):
        with app.app_context():
            # Importing app must not create schema or seed default credentials.
            self.assertEqual(inspect(db.engine).get_table_names(), [])
            runner = app.test_cli_runner()
            self.assertEqual(runner.invoke(args=["init-db"]).exit_code, 0)
            self.assertEqual(runner.invoke(args=["init-db"]).exit_code, 0)
            result = runner.invoke(args=["create-admin", "--username", "owner", "--password", "strong-test-password"])
            self.assertEqual(result.exit_code, 0, result.output)
            duplicate = runner.invoke(args=["create-admin", "--username", "owner", "--password", "strong-test-password"])
            self.assertNotEqual(duplicate.exit_code, 0)
            group = CustomerGroup(name="Retail")
            customer = Customer(name="Test", group=group)
            product = Product(name="Water", cap_type="Blue", bottle_type="Bottle", capacity="20L")
            db.session.add_all([customer, product]); db.session.flush()
            for month in (1, 4, 7, 10):
                sale = Sale(customer_id=customer.id, date_created=datetime(2026, month, 1), total_amount=100)
                db.session.add(sale); db.session.flush()
                db.session.add(SaleItem(sale_id=sale.id, product_id=product.id, quantity=2, price_at_sale=50))
            db.session.add(Purchase(description="Test", total_amount=10, category="Other"))
            db.session.commit()
            compiled = str(select(display_date("%d/%m/%Y %H:%M", Sale.date_created)).compile(dialect=postgresql.dialect()))
            self.assertIn("to_char", compiled)
            self.assertNotIn("strftime", compiled)
            # Verify the existing +7-hour display convention across midnight.
            result = db.session.execute(select(display_date("%d/%m", db.literal(datetime(2026, 1, 1, 20))))).scalar()
            self.assertEqual(result, "02/01")
        client = app.test_client()
        self.assertEqual(client.get("/login").status_code, 200)
        with client.session_transaction() as session:
            session["user_id"] = 1
        urls = ["/", "/sale", "/api/revenue?revenueMetric=product", "/api/revenue?revenuePeriod=quarter"]
        for period in ("day", "month", "year", "hour"):
            urls += [f"/api/sale?salesPeriod={period}", f"/api/expense?expensePeriod={period}"]
        for url in urls:
            response = client.get(url)
            self.assertEqual(response.status_code, 200, url)
        self.assertEqual(client.get("/api/revenue?revenuePeriod=quarter").json["labels"], ["Q1", "Q2", "Q3", "Q4"])
        self.assertEqual(client.get("/api/revenue?revenueMetric=product").json["data"], [400.0])

if __name__ == "__main__":
    unittest.main()
