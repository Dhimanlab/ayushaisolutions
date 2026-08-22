import os
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(_name_)
# Secure fallback key for managing user session cookies
app.secret_key = os.environ.get('SECRET_KEY', 'ayush_dhiman_kangra_ai_secure_2026')

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
        
        # Injects a personalized success alert to the user interface layout
        flash(f"Thank you {name}! Your message has been received by Ayush Dhiman (Kangra).")
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

# 📊 Protected Dashboard Panel Route
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        flash("Please log in to access the dashboard view panel.")
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# 🚪 Log Out Session Destroyer Route
@app.route('/logout')
def logout():
    session.clear()
    flash("You have successfully logged out.")
    return redirect(url_for('login'))

if _name_ == '_main_':
    app.run(debug=True)
