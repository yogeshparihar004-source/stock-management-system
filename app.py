from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DB_PATH = Path(__file__).with_name("stock.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL DEFAULT 'General',
                quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
                price REAL NOT NULL DEFAULT 0 CHECK(price >= 0),
                reorder_level INTEGER NOT NULL DEFAULT 5 CHECK(reorder_level >= 0)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                sold_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)

@app.route("/")
def dashboard():
    with get_db() as db:
        stats = db.execute("""
            SELECT COUNT(*) AS products,
                   COALESCE(SUM(quantity), 0) AS units,
                   COALESCE(SUM(quantity * price), 0) AS value
            FROM products
        """).fetchone()
        low_stock = db.execute("""
            SELECT * FROM products WHERE quantity <= reorder_level
            ORDER BY quantity ASC, name ASC
        """).fetchall()
        recent_sales = db.execute("""
            SELECT sales.*, products.name AS product_name
            FROM sales JOIN products ON products.id = sales.product_id
            ORDER BY sales.id DESC LIMIT 5
        """).fetchall()
    return render_template("dashboard.html", stats=stats, low_stock=low_stock,
                           recent_sales=recent_sales)

@app.route("/products")
def products():
    q = request.args.get("q", "").strip()
    with get_db() as db:
        rows = db.execute("""
            SELECT * FROM products
            WHERE name LIKE ? OR sku LIKE ? OR category LIKE ?
            ORDER BY name
        """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    return render_template("products.html", products=rows, q=q)

@app.route("/products/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        sku = request.form.get("sku", "").strip()
        category = request.form.get("category", "General").strip() or "General"
        try:
            quantity = int(request.form.get("quantity", "0"))
            price = float(request.form.get("price", "0"))
            reorder_level = int(request.form.get("reorder_level", "5"))
            if not name or not sku or quantity < 0 or price < 0 or reorder_level < 0:
                raise ValueError
            with get_db() as db:
                db.execute("""INSERT INTO products
                    (name, sku, category, quantity, price, reorder_level)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (name, sku, category, quantity, price, reorder_level))
            flash("Product added successfully.", "success")
            return redirect(url_for("products"))
        except sqlite3.IntegrityError:
            flash("SKU already exists. Please use a unique SKU.", "danger")
        except (ValueError, TypeError):
            flash("Enter valid values. Quantities and prices cannot be negative.", "danger")
    return render_template("product_form.html", product=None)

@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    with get_db() as db:
        product = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if product is None:
            flash("Product not found.", "danger")
            return redirect(url_for("products"))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            sku = request.form.get("sku", "").strip()
            category = request.form.get("category", "General").strip() or "General"
            try:
                quantity = int(request.form.get("quantity", "0"))
                price = float(request.form.get("price", "0"))
                reorder_level = int(request.form.get("reorder_level", "5"))
                if not name or not sku or quantity < 0 or price < 0 or reorder_level < 0:
                    raise ValueError
                db.execute("""UPDATE products SET name=?, sku=?, category=?, quantity=?,
                    price=?, reorder_level=? WHERE id=?""",
                    (name, sku, category, quantity, price, reorder_level, product_id))
                flash("Product updated successfully.", "success")
                return redirect(url_for("products"))
            except sqlite3.IntegrityError:
                flash("SKU already exists. Please use a unique SKU.", "danger")
            except (ValueError, TypeError):
                flash("Enter valid values. Quantities and prices cannot be negative.", "danger")
    return render_template("product_form.html", product=product)

@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    with get_db() as db:
        sold = db.execute("SELECT COUNT(*) FROM sales WHERE product_id=?", (product_id,)).fetchone()[0]
        if sold:
            flash("This product has sales history and cannot be deleted.", "warning")
        else:
            db.execute("DELETE FROM products WHERE id=?", (product_id,))
            flash("Product deleted.", "success")
    return redirect(url_for("products"))

@app.route("/sales", methods=["GET", "POST"])
def sales():
    with get_db() as db:
        if request.method == "POST":
            try:
                product_id = int(request.form.get("product_id", "0"))
                quantity = int(request.form.get("quantity", "0"))
                product = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
                if not product or quantity <= 0:
                    raise ValueError
                if quantity > product["quantity"]:
                    flash(f"Only {product['quantity']} unit(s) are in stock.", "danger")
                else:
                    db.execute("UPDATE products SET quantity=quantity-? WHERE id=?",
                               (quantity, product_id))
                    db.execute("INSERT INTO sales(product_id, quantity, unit_price) VALUES (?, ?, ?)",
                               (product_id, quantity, product["price"]))
                    flash("Sale recorded and stock updated.", "success")
                    return redirect(url_for("sales"))
            except (ValueError, TypeError):
                flash("Choose a product and enter a quantity greater than zero.", "danger")
        products = db.execute("SELECT * FROM products WHERE quantity > 0 ORDER BY name").fetchall()
        history = db.execute("""
            SELECT sales.*, products.name AS product_name
            FROM sales JOIN products ON products.id = sales.product_id
            ORDER BY sales.id DESC LIMIT 100
        """).fetchall()
    return render_template("sales.html", products=products, sales=history)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
