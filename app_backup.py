from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
import os
import psycopg2
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import razorpay
from supabase import create_client, Client
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import json
import smtplib
from email.message import EmailMessage
from decimal import Decimal
from datetime import timedelta, datetime
from collections import defaultdict
# import matplotlib.pyplot as plt
import io
from supabase import create_client
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
razorpay_client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY"), os.getenv("RAZORPAY_SECRET")))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
mail = Mail(app)

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '123'

users = []

@app.route("/auth/callback")
def auth_callback():
    return render_template("auth_callback.html")

@app.route("/welcome")
def welcome_user():
    if "user" in session:
        return f"✅ Welcome, {session['user']}!"
    return redirect("/user")

@app.route("/sales_chart/<period>")
def sales_chart(period):
    conn = get_connection()
    cur = conn.cursor()

    today = datetime.today()
    if period == "1week":
        since = today - timedelta(days=7)
    elif period == "1month":
        since = today - timedelta(days=30)
    elif period == "6months":
        since = today - timedelta(days=180)
    elif period == "1year":
        since = today - timedelta(days=365)
    else:
        return "Invalid period", 400

    cur.execute("SELECT created_at, total_money FROM orders WHERE created_at >= %s", (since,))
    data = cur.fetchall()
    conn.close()

    daily_sales = defaultdict(float)
    for created, total in data:
        date = created.date()
        daily_sales[date] += float(total)

    dates = sorted(daily_sales.keys())
    values = [daily_sales[date] for date in dates]

    # plt.figure(figsize=(8, 4))
    # plt.plot(dates, values, marker='o', color='green')
    # plt.title(f"Sales Trend ({period})")
    # plt.xlabel("Date")
    # plt.ylabel("Total Money (₹)")
    # plt.xticks(rotation=45)
    # plt.tight_layout()

    # img = io.BytesIO()
    # plt.savefig(img, format="png")
    # img.seek(0)
    return send_file( mimetype="image/png")

@app.route("/store_session", methods=["POST"])
def store_session():
    data = request.json
    email = data.get("email")
    name = data.get("name", "")

    if email:
        session["user"] = email

        # Check if user already exists in oauth_users
        existing = supabase.table("oauth_users").select("id").eq("email", email).execute()
        if not existing.data:
            # Insert into oauth_users
            supabase.table("oauth_users").insert({
                "email": email,
                "name": name
            }).execute()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

def serialize_product(product):
    return {
        "id": product["id"],
        "name": product["name"],
        "price": float(product["price"]) if isinstance(product["price"], Decimal) else product["price"],
        "description": product["description"],
        "image": product["image"]
    }

def get_connection():
    return psycopg2.connect("postgresql://postgres.kfdqdghuwhvjuafdpgis:Deepika%4029092003@aws-0-ap-south-1.pooler.supabase.com:6543/postgres")

def get_user_by_id(user_id):
    result = supabase.table("users").select("*").eq("id", user_id).single().execute()
    return result.data if result.data else None
def get_product_by_id(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, image FROM products WHERE id = %s", (product_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'id': str(row[0]), 'name': row[1], 'price': row[2], 'image': row[3], 'quantity': 1}
    return None
def get_products(category=None, limit=None):
    conn = get_connection()
    cursor = conn.cursor()
    if category and category != "All":
        query = "SELECT id, name, price, image FROM products WHERE category = %s"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query, (category,))
    else:
        query = "SELECT id, name, price, image FROM products"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    products = [dict(zip(columns, row)) for row in rows]
    return products
def get_cart_products(cart_dict):
    if not cart_dict:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    query = f"SELECT id, name, price, image FROM products WHERE id IN ({','.join(['%s']*len(cart_dict))})"
    cursor.execute(query, list(cart_dict.keys()))
    products = cursor.fetchall()
    conn.close()
    cart_items = []
    for p in products:
        pid = str(p[0])
        quantity = cart_dict[pid]
        subtotal = p[2] * quantity
        cart_items.append({
            'id': p[0], 'name': p[1], 'price': p[2],
            'image': p[3], 'quantity': quantity, 'subtotal': subtotal
        })
    return cart_items
@app.context_processor
def inject_user_session():
    return dict(session_user=session.get("user_id"))  # Still useful for global templates if needed


@app.route("/")
def home():
    print("🔐 Session contents:", session)
    print("🆔 Logged-in user ID:", session.get("user_id"))

    user_id = session.get("user_id")
    name = None

    if user_id:
        # Try to fetch name from 'users' table using ID
        response = supabase.table("users").select("name").eq("id", user_id).execute()
        if response.data:
            name = response.data[0]['name']
        else:
            # Fallback to 'oauth_users' table
            response = supabase.table("oauth_users").select("name").eq("id", user_id).execute()
            if response.data:
                name = response.data[0]['name']

    return render_template("home.html", user=name)

@app.route("/terms-and-conditions")
def terms_and_conditions():
    return render_template("terms_and_conditions.html")

@app.route("/shop")
def shop():
    category = request.args.get('category', 'All')
    products = get_products(category)
    return render_template("shop.html", products=products, selected_category=category)

@app.route("/product_chart/<period>")
def product_chart(period):
    conn = get_connection()
    cursor = conn.cursor()
    
    today = datetime.today()
    if period == "1month":
        since = today - timedelta(days=30)
    else:
        since = today - timedelta(days=365)

    cursor.execute("""
        SELECT product_name, SUM(quantity) FROM order_items
        JOIN orders ON orders.id = order_items.order_id
        WHERE orders.created_at >= %s
        GROUP BY product_name
    """, (since,))
    
    data = cursor.fetchall()
    conn.close()

    labels = [row[0] for row in data]
    values = [row[1] for row in data]

    # # Pie chart
    # fig, ax = plt.subplots()
    # ax.pie(values, labels=labels, autopct='%1.1f%%')
    # ax.set_title("Product Distribution")

    # img = io.BytesIO()
    # plt.savefig(img, format="png")
    # img.seek(0)
    return send_file( mimetype="image/png")

@app.route('/product/<int:product_id>')
def product(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    cursor.execute("SELECT * FROM products WHERE id != %s LIMIT 3", (product_id,))
    recommended_items = cursor.fetchall()
    conn.close()
    if product:
        return render_template('product.html', product=product, recommended_items=recommended_items)
    else:
        return "Product not found", 404

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'cart' not in session or not isinstance(session['cart'], dict):
        session['cart'] = {}
    cart = session['cart']
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session and str(product_id) in session['cart']:
        session['cart'].pop(str(product_id))
        session.modified = True
    return jsonify({'success': True})

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    for product_id, quantity in cart.items():
        product = get_product_by_id(product_id)
        if product:
            product['quantity'] = quantity
            product['subtotal'] = product['price'] * quantity
            total += product['subtotal']
            cart_items.append(product)
    return render_template('cart.html', products=cart_items, total=total)

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Helper to get user
def get_user_by_id(user_id):
    result = supabase.table("users").select("*").eq("id", user_id).single().execute()
    return result.data if result.data else None

@app.route('/checkout', methods=['GET'])
def checkout():
    cart = session.get('cart', {})
    products = get_cart_products(cart)
    subtotal = sum(item['subtotal'] for item in products)
    shipping = 70
    total = subtotal + shipping

    razorpay_order = razorpay_client.order.create(dict(
        amount=total * 100, currency="INR", payment_capture='1'))
    razorpay_order_id = razorpay_order['id']
    callback_url = "/payment_success"

    # ✅ Fetch user data from Supabase using session['user_id']
    user = get_user_by_id(session['user_id']) if 'user_id' in session else None
    print("User ID in session:", session.get('user_id'))
    return render_template('checkout.html',
                           products=products,
                           subtotal=subtotal,
                           shipping=shipping,
                           total=total,
                           razorpay_order_id=razorpay_order_id,
                           key_id=os.getenv("RAZORPAY_KEY"),
                           callback_url=callback_url,
                           user=user)

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect('/user')

    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    street_address = request.form['address']
    city = request.form['city']
    state = request.form['state']
    pincode = request.form['pincode']
    payment_method = request.form.get('payment', 'COD')

    cart = session.get('cart', {})
    products = get_cart_products(cart)  # Your function to fetch product info
    subtotal = sum(item['subtotal'] for item in products)
    shipping_fee = 70
    total = subtotal + shipping_fee
    order_details = json.dumps(products)

    # Insert into Supabase
    supabase.table('orders').insert({
        "name": name,
        "email": email,
        "phone": phone,
        "street_address": street_address,
        "city": city,
        "state": state,
        "pincode": pincode,
        "order_details": order_details,
        "total_money": total,
        "is_paid": payment_method == "UPI",
        "status": "pending"
    }).execute()

    # Format product details
    product_lines = "\n".join([
        f"- {item['name']} × {item['quantity']} = ₹{item['subtotal']}"
        for item in products
    ])

    # Email body content
    email_body = f"""
🧾 New Order Received!

👤 Customer:
Name: {name}
Email: {email}
Phone: {phone}

🏠 Address:
{street_address}, {city}, {state} - {pincode}

💳 Payment Method: {payment_method}

📦 Order Summary:
{product_lines}

Subtotal: ₹{subtotal}
Shipping: ₹{shipping_fee}
Grand Total: ₹{total}
    """

    # Send email
    try:
        msg = Message(subject="🧾 New Order Received - Puvana's Macrame",
                      sender='puvanasmacrame@gmail.com',  # Replace
                      recipients=['puvanasmacrame@gmail.com'],
                      body=email_body)
        mail.send(msg)
    except Exception as e:
        print("Mail sending failed:", e)

    # Clear cart
    session.pop('cart', None)
    return redirect('/thank_you')

@app.route('/payment_success', methods=['GET', 'POST'])
def payment_success():
    try:
        print("✅ Entered payment_success route")

        cart = session.get('cart', {})
        print("Cart:", cart)

        if not cart:
            return "❌ Cart is empty or session expired", 400

        products = get_cart_products(cart)
        total = sum(item['subtotal'] for item in products)
        items_summary = ", ".join([f"{item['name']} x{item['quantity']}" for item in products])

        user = session.get('user')
        customer_name = user if isinstance(user, str) else user.get('name', 'Guest')

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (customer_name, items, total) VALUES (%s, %s, %s)",
            (customer_name, items_summary, total)
        )
        conn.commit()
        conn.close()

        session.pop('cart', None)

        return render_template('payment_success.html', name=customer_name)

    except Exception as e:
        print("❌ Payment success error:", e)
        return "Internal Server Error", 500

@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    # --- Handle POST: Login or Product Addition ---
    if request.method == "POST":
        if not session.get("authenticated"):
            # --- Admin Login ---
            username = request.form.get("username")
            password = request.form.get("password")
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session["authenticated"] = True
            else:
                return render_template("admin.html", show_form=False, error="❌ Wrong username or password.")
        else:
            # --- Add Product ---
            try:
                category = request.form["category"]
                name = request.form["name"]
                price = float(request.form["price"])
                description = request.form["description"]
                image_file = request.files.get("image")

                # Upload image to Supabase
                if image_file and image_file.filename:
                    filename = secure_filename(image_file.filename.replace(" ", "_"))
                    image_data = image_file.read()
                    supabase.storage.from_('product-images').upload(
                        f'products/{filename}', image_data,
                        file_options={"content-type": image_file.mimetype}
                    )
                    image_url = supabase.storage.from_('product-images').get_public_url(f'products/{filename}')
                else:
                    image_url = ""

                # Check for duplicate product
                existing = supabase.table("products").select("*").eq("name", name).execute().data
                if existing:
                    return "<script>alert('❌ Duplicate product detected.'); window.location.href='/admin';</script>"

                # Insert into DB
                supabase.table("products").insert({
                    "category": category,
                    "name": name,
                    "price": price,
                    "description": description,
                    "image": image_url
                }).execute()

                return "<script>alert('✅ Product added successfully!'); window.location.href='/admin';</script>"

            except Exception as e:
                return f"<script>alert('⚠️ Error: {str(e)}'); window.location.href='/admin';</script>"

    # --- Handle GET ---
    if session.get("authenticated"):
        view = request.args.get("view", "orders")

        # Fetch products
        try:
            products_data = supabase.table("products").select("*").order("id", desc=True).execute().data
        except Exception as e:
            products_data = []
            print(f"[Error] Fetching products: {e}")

        # Initialize order lists
        orders_pending, orders_making, orders_delivery = [], [], []

        # Always fetch orders when logged in
        try:
            orders_data = supabase.table("orders").select("*").order("id", desc=True).execute().data

            for o in orders_data:
                try:
                    details = json.loads(o["order_details"]) if isinstance(o["order_details"], str) else o["order_details"]
                except Exception:
                    details = []

                order_dict = {
                    'id': o["id"],
                    'name': o["name"],
                    'email': o["email"],
                    'phone': o["phone"],
                    'address': f"{o['street_address']}, {o['city']}, {o['state']} - {o['pincode']}",
                    'is_paid': o["is_paid"],
                    'details': details,
                    'total': o["total_money"],
                    'status': o["status"]
                }

                if o["status"] == "pending":
                    orders_pending.append(order_dict)
                elif o["status"] == "in_making":
                    orders_making.append(order_dict)
                elif o["status"] == "out_for_delivery":
                    orders_delivery.append(order_dict)

        except Exception as e:
            print(f"[Error] Fetching orders: {e}")

        # Render dashboard
        return render_template("admin.html",
                               show_form=True,
                               products=products_data,
                               orders_pending=orders_pending,
                               orders_making=orders_making,
                               orders_delivery=orders_delivery,
                               show_add_product=(view == "add"))

    # --- Not Authenticated Yet ---
    return render_template("admin.html", show_form=False)

@app.route("/edit_product", methods=["POST"])
def edit_product():
    product_id = request.form.get("id")
    name = request.form.get("name")
    price = request.form.get("price")
    description = request.form.get("description")
    image = request.files.get("image")

    image_url = None
    if image and image.filename:
        filename = secure_filename(image.filename)
        file_path = f"product_images/{filename}"
        supabase.storage().from_("your-bucket").upload(file=image, path=file_path)
        image_url = supabase.storage().from_("your-bucket").get_public_url(file_path)

    update_data = {
        "name": name,
        "price": float(price),
        "description": description,
    }
    if image_url:
        update_data["image"] = image_url

    supabase.table("products").update(update_data).eq("id", product_id).execute()
    return redirect("/admin")

@app.route("/delete_product", methods=["POST"])
def delete_product():
    product_id = request.form["id"]
    supabase.table("products").delete().eq("id", product_id).execute()
    return redirect("/admin")

@app.route("/update_order_status", methods=["POST"])
def update_order_status():
    data = request.get_json()
    order_id = data.get("order_id")
    new_status = data.get("new_status")

    if not order_id or not new_status:
        return jsonify({"message": "Invalid request"}), 400

    try:
        supabase.table("orders").update({"status": new_status}).eq("id", order_id).execute()
        return jsonify({"message": "✅ Order status updated!"})
    except Exception as e:
        print("Error updating order:", e)
        return jsonify({"message": "❌ Failed to update order"}), 500


@app.route('/user')
def user():
    return render_template("user.html")  # Login/signup page

@app.route("/user/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    print("Login attempt - Username:", username, "Password:", password)
    # Fetch from Supabase using username (or email)
    response = supabase.table("users").select("*").eq("username", username).execute()
    print("Supabase Response:", response)
    if response.data and len(response.data) > 0:
        user = response.data[0]
        if user.get("password") == password:  # You should hash this later
            session["user_id"] = user["id"]  # ✅ Now we store user_id for checkout autofill
            flash(f"✅ Welcome, {user['name'].split()[0]}!")
            return redirect("/")
        else:
            flash("❌ Incorrect password.")
    else:
        flash("❌ User not found.")
    return redirect("/user")

@app.route('/user/signup', methods=['POST'])
def user_signup():
    fullname = request.form['fullname']
    email = request.form['email']
    raw_password = request.form['password']
    password = generate_password_hash(raw_password)
    for user in users:
        if user['email'] == email:
            return "⚠️ Email already registered. Try logging in."
    users.append({'fullname': fullname, 'email': email, 'password': password})
    return "<script>alert('✅ Signup successful. Please login.'); window.location.href='/user';</script>"

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        email = request.form["email"]
        phone = request.form["phone"]
        raw_password = request.form["password"]
        password = generate_password_hash(raw_password)

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (name, username, email, phone, password) VALUES (%s, %s, %s, %s, %s)",
                (name, username, email, phone, password)
            )
            conn.commit()
        except psycopg2.errors.UniqueViolation as e:
            conn.rollback()
            if 'username' in str(e):
                error_msg = "❌ Username already taken."
            elif 'phone' in str(e):
                error_msg = "❌ Phone number already registered."
            elif 'email' in str(e):
                error_msg = "❌ Email already used."
            else:
                error_msg = "❌ Registration failed."
            return render_template("signup.html", error=error_msg)
        except Exception as e:
            conn.rollback()
            return render_template("signup.html", error=f"⚠️ Unexpected error: {e}")
        finally:
            conn.close()

        return redirect("/user")

    return render_template("signup.html")

def get_order_by_id(order_id):
    # Get the order
    order_response = supabase.table("orders").select("*").eq("id", order_id).single().execute()
    order_data = order_response.data
    if not order_data:
        return None
    # Parse order_details from JSON/text
    try:
        order_data["details"] = json.loads(order_data["order_details"])
    except Exception as e:
        order_data["details"] = []
        print("⚠️ Failed to parse order_details:", e)
    return order_data

@app.route("/order/<int:order_id>")
def order_details(order_id):
    order = get_order_by_id(order_id)  # Replace this with your actual data fetching
    return render_template("order_details.html", order=order)


@app.route("/profile")
def profile():
    print("Current session:", session)  # 🪵 Debug session

    user_id = session.get("user_id")
    if not user_id:
        return redirect("/user")

    # 🔍 Try to fetch user details from 'users' by ID
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    user = response.data[0] if response.data else None

    # 🔁 Fallback to 'oauth_users' table
    if not user:
        response = supabase.table("oauth_users").select("*").eq("id", user_id).execute()
        user = response.data[0] if response.data else None

    if not user:
        flash("User not found.")
        return redirect("/user")

    # 📦 Fetch orders using email from the retrieved user
    user_email = user.get("email", "")
    order_response = supabase.table("orders").select("*").eq("email", user_email).order("id", desc=True).execute()
    orders = order_response.data if order_response.data else []

    # 🧾 Parse order_details safely
    for order in orders:
        try:
            order["details"] = json.loads(order["order_details"])
        except Exception:
            order["details"] = []

    return render_template("profile.html", user=user, orders=orders)



@app.route("/profile/update", methods=["POST"])
def update_profile():
    if "user" not in session:
        return redirect("/user")

    user_email = session["user"]

    # Form data
    name = request.form["name"]
    username = request.form["username"]
    email = request.form["email"]
    phone = request.form["phone"]
    address = request.form.get("address", "")
    password = request.form.get("password", "")

    update_data = {
        "name": name,
        "username": username,
        "email": email,
        "phone": phone,
        "address": address
    }
    if password:
        update_data["password"] = password

    try:
        # First check if user exists
        existing = supabase.table("users").select("id").eq("email", user_email).execute()

        if not existing.data:
            # Insert new user if not found
            supabase.table("users").insert({
                **update_data,
                "password": password or "google-auth"
            }).execute()
        else:
            # Update existing user
            supabase.table("users").update(update_data).eq("email", user_email).execute()

        # Update session if email changed
        if email != user_email:
            session["user"] = email

        flash("Profile updated successfully.")
    except Exception as e:
        flash(f"Error updating profile: {str(e)}")

    return redirect("/profile")

@app.route("/test_db")
def test_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products LIMIT 1")
        product = cursor.fetchone()
        conn.close()
        return f"✅ DB Connected! Sample product: {product}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    session.clear()
    flash("You have been logged out.")
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)