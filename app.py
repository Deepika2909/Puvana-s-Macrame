from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'puvanasmacrame@gmail.com'     # your email
app.config['MAIL_PASSWORD'] = 'wiqscffrmtoadumm'          # generate App Password
mail = Mail(app)


app.secret_key = "puvanasmacrame"

UPLOAD_FOLDER = "static"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_products(category=None, limit=None):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    if category and category != "All":
        query = "SELECT id, name, price, image FROM products WHERE category = ?"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query, (category,))
    else:
        query = "SELECT id, name, price, image FROM products"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)
    products = cursor.fetchall()
    conn.close()
    return products

def get_cart_products(cart_ids):
    if not cart_ids:
        return []
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    query = f"SELECT id, name, price, image FROM products WHERE id IN ({','.join(['?']*len(cart_ids))})"
    cursor.execute(query, cart_ids)
    products = cursor.fetchall()
    conn.close()
    return products

@app.route("/")
def index():
    products = get_products(limit=12)
    return render_template("index.html", products=products)

@app.route("/shop")
def shop():
    category = request.args.get('category', 'All')
    products = get_products(category)
    return render_template("shop.html", products=products, selected_category=category)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(product_id)
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session:
        session['cart'] = [pid for pid in session['cart'] if pid != product_id]
        session.modified = True
    return redirect(url_for('cart'))

@app.route("/cart")
def cart():
    cart_ids = session.get('cart', [])
    products = get_cart_products(cart_ids)
    return render_template("cart.html", products=products)

@app.route('/product/<int:product_id>')
def product(product_id):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    cursor.execute("SELECT * FROM products WHERE id != ? LIMIT 3", (product_id,))
    recommended_items = cursor.fetchall()
    conn.close()
    if product:
        return render_template('product.html', product=product, recommended_items=recommended_items)
    else:
        return "Product not found", 404

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        category = request.form["category"]
        name = request.form["name"]
        price = float(request.form["price"])
        description = request.form["description"]

        image_file = request.files.get("image")
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename.replace(" ", "_"))
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_name = filename
        else:
            image_name = ""

        conn = sqlite3.connect("products.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM products WHERE name = ? OR description = ?", (name, description))
        existing = cursor.fetchone()

        if existing:
            conn.close()
            return "<script>alert('❌ Duplicate product detected. Not added.'); window.location.href='/admin';</script>"

        cursor.execute("INSERT INTO products (category, name, price, image, description) VALUES (?, ?, ?, ?, ?)",
                       (category, name, price, image_name, description))
        conn.commit()
        conn.close()

        return "<script>alert('✅ Product added successfully!'); window.location.href='/admin';</script>"

    return render_template("admin.html")

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        contact = request.form.get('contact')
        total = request.form.get('total')

        if not total:
            return "❌ Error: Total amount missing!", 400

        cart_ids = session.get('cart', [])
        products = get_cart_products(cart_ids)

        # HTML email body
        html = f"""
        <h2>🧾 Order Summary</h2>
        <p><strong>Name:</strong> {name}<br>
        <strong>Address:</strong> {address}<br>
        <strong>Contact:</strong> {contact}</p>
        <hr>
        <ul style="list-style:none;padding-left:0;">
        """
        for p in products:
            html += f"""
            <li style="margin-bottom: 15px;">
                <strong>{p[1]}</strong><br>
                <img src="https://yourdomain.com/static/{p[3]}" width="120"><br>
                Price: ₹{p[2]}
            </li>
            """
        html += f"</ul><h3>💵 Total: ₹{total}</h3>"

        msg = Message("🧶 New Order - Puvana's Macrame",
                      sender='puvanasmacrame@gmail.com',
                      recipients=['puvanasmacrame@gmail.com'])
        msg.html = html

        try:
            mail.send(msg)
        except Exception as e:
            return f"❌ Email sending failed: {e}", 500

        session['cart'] = []  # Clear cart after order
        return render_template('confirm.html', name=name)

    total = request.args.get('total')
    return render_template('checkout.html', total=total)

if __name__ == "__main__":
    app.run(debug=True)

