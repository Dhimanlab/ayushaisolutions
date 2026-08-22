import os
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ayush_dhiman_kangra_ai_secure_2026')

# 🧠 Live Memory Storage Layers (Bypasses Render's Read-Only File System Entirely!)
if not hasattr(app, 'contact_messages'):
    app.contact_messages = []
if not hasattr(app, 'business_ledger'):
    app.business_ledger = []

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
        
        # Save straight to RAM memory buffer matrix
        app.contact_messages.append({
            'name': name,
            'email': email,
            'phone': phone if phone else 'N/A',
            'message': message
        })
        
        flash(f"Thank you {name}! Your message has been received by Ayush Dhiman (Kangra).")
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

# 📊 Protected Dashboard Gateway Panel
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        flash("Please log in to access the dashboard view panel.")
        return redirect(url_for('login'))
    
    # Safely pull memory structures without standard disk I/O bottlenecks
    messages = app.contact_messages[::-1]  # Show newest first
    records = app.business_ledger[::-1]
    
    # Calculate counters dynamically out of live memory arrays
    msg_count = len(messages)
    record_count = len(records)
    
    total_unpaid = sum(float(rec['amount_due']) for rec in records if rec['payment_status'] == 'Unpaid')
    
    return render_template(
        'dashboard.html', 
        messages=messages, 
        records=records, 
        msg_count=msg_count, 
        record_count=record_count, 
        total_unpaid=total_unpaid
    )

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
    
    # Log object array down to system active variables
    app.business_ledger.append({
        'client_name': c_name,
        'business_type': b_type,
        'item_description': i_desc,
        'amount_due': amt,
        'payment_status': status
    })
    
    flash("New transaction invoice ledger logged into universal business records successfully!")
    return redirect(url_for('dashboard'))

# 🚪 Log Out Session Destroyer Route
@app.route('/logout')
def logout():
    session.clear()
    flash("You have successfully logged out.")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
