import os
import io
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import google.generativeai as genai
from pypdf import PdfReader

app = Flask(__name__)
CORS(app)

# ========== CONFIG ==========
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ayush-ai-solutions-super-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ayushai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Gemini (keep your existing key)
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

document_context = ""

# ========== USER MODEL ==========
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()

# ========== PUBLIC PAGES ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/products')
def products():
    return render_template('products.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ========== AUTHENTICATION ==========
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()

        if not username or not email or not password:
            flash('Please fill all required fields.', 'danger')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, email=email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

# ========== AI ROUTES (kept from your original) ==========
@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    global document_context
    if 'pdf' not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files['pdf']
    if file.filename == '':
        return jsonify({"error": "No file selected."}), 400

    try:
        pdf_stream = io.BytesIO(file.read())
        reader = PdfReader(pdf_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        document_context = text

        if len(document_context) > 12000:
            return jsonify({"error": "Document too large for free tier."}), 403

        if not document_context.strip():
            return jsonify({"error": "Could not extract text from PDF."}), 400

        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"Summarize this text concisely using structured bullet points:\n\n{document_context}"
        )
        return jsonify({"summary": response.text})
    except Exception as e:
        print(f"PDF Error: {e}")
        return jsonify({"error": "Unable to process document."}), 500

@app.route('/api/chat', methods=['POST'])
def chat_pdf():
    global document_context
    if not document_context:
        return jsonify({"error": "Please upload a document first."}), 400

    data = request.json or {}
    question = data.get('question')
    if not question:
        return jsonify({"error": "Question is empty."}), 400

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"Context Document:\n{document_context}\n\nQuestion: {question}\nAnswer strictly based on the document."
        )
        return jsonify({"answer": response.text})
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({"error": "AI service failed."}), 500

# ========== RUN ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
