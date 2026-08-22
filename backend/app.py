import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(_name_)
# Secure fallback key for managing user session cookies
app.secret_key = os.environ.get('SECRET_KEY', 'ayush_dhiman_kangra_ai_secure_2026')

DB_FILE = 'database.db'

def init_db():
    """Initializes the database and creates the messages table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()

# Initialize the storage database tables instantly on startup
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
        
        # Save contact form submission securely into the database
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
        except Exception as e:
            flash("An error occurred while saving your message. Please try again.")
            
        return redirect(url_for('home'))
    return render_template('contact.html')

# 🔒 Client Portal Login Route & Verification
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Administrative owner credentials configuration for Ayush Dhiman
        if username == "ayush" and password == "kangra123":
            session['logged_in'] = True
            session['username'] = "Ayush Dhiman"
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password. Please try again.")
            return redirect(url_for('login'))
            
    return render_template('login.html')

# 📊 Protected Dashboard Panel Route with Database Inbox Viewer
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        flash("Please log in to access the dashboard view panel.")
        return redirect(url_for('login'))
    
    # Retrieve all contact form messages from the database to display to Ayush
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contact_messages ORDER BY submitted_at DESC')
    messages = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard.html', messages=messages)

# 🚪 Log Out Session Destroyer Route
@app.route('/logout')
def logout():
    session.clear()
    flash("You have successfully logged out.")
    return redirect(url_for('login'))

if _name_ == '_main_':
    app.run(debug=True)
