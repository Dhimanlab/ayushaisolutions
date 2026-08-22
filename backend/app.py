import os
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ayush_dhiman_kangra_ai_secure_2026')

# Live Memory Storage Layers (Bypasses Render's read-only File System entirely)
if not hasattr(app, 'contact_messages'):
    app.contact_messages = []
if not hasattr(app, 'business_ledger'):
    app.business_ledger = []

# Main Landing Page Route
@app.route('/')
def home():
    return render_template('index.html')

# About Us Page Route
@app.route('/about')
def about():
    return render_template('about.html')

# Products Page Route
@app.route('/products')
def products():
    return render_template('products.html')

# Pricing Page Route
@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# Contact Us Page Route
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Save message to in-memory list
        app.contact_messages.append({
            'name': name,
            'email': email,
            'message': message
        })
        flash('Your message has been sent successfully!')
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

# User Authentication Page Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Replace 'admin' and 'password123' with your preferred secure credentials
        if username == 'admin' and password == 'password123':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))
            
    return render_template('login.html')

# Secure Management Dashboard Route
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        flash('Access denied. Please log in first.')
        return redirect(url_for('login'))
        
    return render_template(
        'dashboard.html', 
        messages=app.contact_messages, 
        ledger=app.business_ledger
    )

# User Session Logout Route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))
