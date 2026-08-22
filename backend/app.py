import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ayush_dhiman_kangra_ai_secure_2026')

DB_FILE = 'database.db'

def init_db():
    """Initializes clean database table paths layout structures."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 📬 Re-create Universal Client Inquiry Inbox Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            message TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 📊 Re-create Universal Business Transactions & Ledger Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS business_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            business_type TEXT NOT NULL,
            item_description TEXT NOT NULL,
            amount_due REAL DEFAULT 0.0,
            payment_status TEXT DEFAULT 'Unpaid',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize tables cleanly on application boot sequence execution loops
init_db()

# 🏠 Main Landing Page Route
@app.route('/')
def home():
    return render_template('index.html')

# ℹ️ About Us Page Route
@app.route('/about')
def about():
    return render_template('about.html')

# 🤖 Products Showcase Route
@app.route('/products')
def products():
    return render_template('products.html')

# 💳 Subscription Pricing Route
@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# 📞 Business Contact Route & Form Handling
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contact_messages (name, email, phone, message)
                VALUES (?, ?, ?, ?)
            ''', (name, email, phone, message))
            conn.commit()
            conn.close()
            flash(f"Thank you {name}! Your message has been saved and received by Ayush Dhiman (Kangra).")
        except Exception:
            flash("An error occurred while saving your message. Please try again.")
            
        return redirect(url_for('home'))
    return render_template('contact.html')

# 🔒 Client Portal Login Route & Verification
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == "ayush" and password == "kangra123":
            session['logged_in'] = True
            session['username'] = "Ayush Dhiman"
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password. Please try again.")
            return redirect(url_for('login'))
            
    return render_template('login.html')

# 📊 Protected Dashboard Control Gateway Panel
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        flash("Please log in to access the dashboard view panel.")
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Safely calculate total messages count and isolate index
    cursor.execute('SELECT COUNT(*) FROM contact_messages')
    res1 = cursor.fetchone()
    msg_count = res1[0] if res1 else 0
    
    # Safely calculate total transaction logs count and isolate index
    cursor.execute('SELECT COUNT(*) FROM business_ledger')
    res2 = cursor.fetchone()
    record_count = res2[0] if res2 else 0
    
    # Safely calculate total uncollected revenue value float indices
    cursor.execute("SELECT SUM(amount_due) FROM business_ledger WHERE payment_status = 'Unpaid'")
    res3 = cursor.fetchone()
    total_unpaid = res3[0] if res3 and res3[0] is not None else 0.0
    conn.close()
    
    # Fetch lists inside separate stream to allow safe rendering row logic arrays
    conn_list = sqlite3.connect(DB_FILE)
    conn_list.row_factory = sqlite3.Row
    cursor_list = conn_list.cursor()
    
    cursor_list.execute('SELECT * FROM contact_messages ORDER BY submitted_at DESC')
    messages = cursor_list.fetchall()
    
    cursor_list.execute('SELECT * FROM business_ledger ORDER BY created_at DESC')
    records = cursor_list.fetchall()
    conn_list.close()
    
    return render_template('dashboard.html', messages=messages, records=records, msg_count=msg_count, record_count=record_count, total_unpaid=total_unpaid)

# 🧾 Add Universal Record Action Router Handler (Supports any enterprise)
@app.route('/dashboard/add_record', methods=['POST'])
def add_business_record():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    c_name = request.form.get('client_name')
    b_type = request.form.get('business_type')
    i_desc = request.form.get('item_description')
    amt = request.form.get('amount_due', 0.0)
    status = request.form.get('payment_status', 'Unpaid')
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO business_ledger (client_name, business_type, item_description, amount_due, payment_status)
            VALUES (?, ?, ?, ?, ?)
        ''', (c_name, b_type, i_desc, amt, status))
        conn.commit()
        conn.close()
        flash("New transaction invoice ledger logged into universal business records.")
    except Exception:
        flash("Failed to store general transaction entry block.")
        
    return redirect(url_for('dashboard'))

# 🚪 Log Out Session Destroyer Route
@app.route('/logout')
def logout():
    session.clear()
    flash("You have successfully logged out.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
