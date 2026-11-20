import os
import io
import re
import sqlite3
import smtplib
from datetime import datetime
from email.message import EmailMessage

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import google.generativeai as genai
from pypdf import PdfReader

app = Flask(__name__)
CORS(app)

# ================= CONFIG =================
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

# ================= USER MODEL =================
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

# ================= ENQUIRY & EMAIL SETUP =================
DB_PATH = os.environ.get("ENQUIRY_DB", "enquiries.db")

def init_enquiry_db():
    with sqlite3.connect(DB_PATH) as db_conn:
        db_conn.execute("""CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, name TEXT,
            phone TEXT, email TEXT, product TEXT, message TEXT)""")

def send_alert_email(r):
    host, user = os.environ.get("SMTP_HOST"), os.environ.get("SMTP_USER")
    pw, to = os.environ.get("SMTP_PASS"), os.environ.get("ALERT_TO")
    if not (host and user and pw and to):
        return
    m = EmailMessage()
    m["Subject"] = "New enquiry from " + r["name"]
    m["From"], m["To"] = user, to
    m.set_content("Name: %s\nPhone: %s\nEmail: %s\nInterested in: %s\n\n%s" %
                  (r["name"], r["phone"], r["email"] or "-", r["product"], r["message"] or "-"))
    try:
        with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587")), timeout=10) as s:
            s.starttls()
            s.login(user, pw)
            s.send_message(m)
    except Exception as e:
        print("Email failed:", e)

init_enquiry_db()

# ================= PUBLIC PAGES =================
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

@app.route('/programs')
def programs():
    return render_template('program.html')

@app.route('/api/enquiry', methods=['POST'])
def api_enquiry():
    d = request.get_json(silent=True) or {}
    if (d.get("website") or "").strip():
        return jsonify(ok=True)
    name = (d.get("name") or "").strip()[:80]
    phone = re.sub(r"\D", "", d.get("phone") or "")[-10:]
    email = (d.get("email") or "").strip()[:120]
    product = (d.get("product") or "").strip()[:60]
    message = (d.get("message") or "").strip()[:1000]
    if not name:
        return jsonify(ok=False, error="Please enter your name."), 400
    if not re.fullmatch(r"[6-9]\d{9}", phone):
        return jsonify(ok=False, error="Please enter a valid 10-digit mobile number."), 400
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return jsonify(ok=False, error="Please enter a valid email address."), 400
    row = dict(name=name, phone=phone, email=email, product=product, message=message)
    with sqlite3.connect(DB_PATH) as db_conn:
        db_conn.execute(
            "INSERT INTO enquiries (created_at,name,phone,email,product,message) VALUES (?,?,?,?,?,?)",
            (datetime.utcnow().isoformat(timespec="seconds"), name, phone, email, product, message)
        )
    send_alert_email(row)
    return jsonify(ok=True)# ================= AUTHENTICATION =================
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

        user = User.query.filter((User.username == username) | (User.email == username)).first()
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

# ================= AI ROUTES =================
@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    global document_context
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file uploaded.'}), 400
    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400
    try:
        pdf_stream = io.BytesIO(file.read())
        reader = PdfReader(pdf_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        if len(document_context) > 12000:
            return jsonify({'error': 'Document too large for free tier.'}), 400
        document_context = text
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"Summarize this text concisely using structured bullet points:\n\n{document_context}"
        )
        return jsonify({'summary': response.text})
    except Exception as e:
        print(f"PDF Error: {e}")
        return jsonify({'error': 'Unable to process document.'}), 500

@app.route('/api/chat', methods=['POST'])
def chat_pdf():
    global document_context
    if not document_context:
        return jsonify({'error': 'Please upload a document first.'}), 400
    data = request.get_json() or {}
    question = data.get('question')
    if not question:
        return jsonify({'error': 'Question is empty.'}), 400
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"Context: {document_context}\nQuestion: {question}\nAnswer strictly based on the document."
        )
        return jsonify({'answer': response.text})
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({'error': 'AI service failed.'}), 500
@app.route('/programs/officers-mess')
def officers_mess():
    return render_template('officers-mess.html')

# ================= OFFICER'S MESS MANAGEMENT ERP (ALL 8 MODULES) =================
import csv
import io
from datetime import datetime
from flask import Response

class MessMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_no = db.Column(db.String(50), nullable=False)
    rank = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    living_status = db.Column(db.String(40), default='Living-In')
    monthly_sub = db.Column(db.Float, default=1500.0)

class MessRation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), default='Dry Ration')
    item_name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), default='kg')
    opening = db.Column(db.Float, default=0.0)
    receipt = db.Column(db.Float, default=0.0)
    issued = db.Column(db.Float, default=0.0)
    rate = db.Column(db.Float, default=0.0)
    min_level = db.Column(db.Float, default=10.0)

class MessingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, nullable=False)
    officer_name = db.Column(db.String(120), nullable=False)
    meal_type = db.Column(db.String(80), nullable=False)
    headcount = db.Column(db.Integer, default=1)
    amount = db.Column(db.Float, default=0.0)
    remarks = db.Column(db.String(200), default='')
    date_str = db.Column(db.String(30), default=lambda: datetime.utcnow().strftime('%Y-%m-%d'))

class MessGuestRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_no = db.Column(db.String(30), nullable=False)
    member_id = db.Column(db.Integer, nullable=False)
    officer_name = db.Column(db.String(120), nullable=False)
    guest_name = db.Column(db.String(120), nullable=False)
    days = db.Column(db.Integer, default=1)
    tariff = db.Column(db.Float, default=800.0)
    status = db.Column(db.String(30), default='Occupied')

class MessAuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.String(40), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

with app.app_context():
    db.create_all()

def log_mess_audit(module, details):
    entry = MessAuditLog(module=module, details=details)
    db.session.add(entry)
    db.session.commit()

@app.route('/officers-mess/app')
def officers_mess_app():
    members = MessMember.query.all()
    rations = MessRation.query.all()
    messing_logs = MessingLog.query.order_by(MessingLog.id.desc()).all()
    rooms = MessGuestRoom.query.order_by(MessGuestRoom.id.desc()).all()
    audits = MessAuditLog.query.order_by(MessAuditLog.id.desc()).limit(50).all()

    low_stock_count = sum(1 for r in rations if (r.opening + r.receipt - r.issued) <= r.min_level)
    total_messing = sum(l.amount for l in messing_logs)
    occupied_rooms = sum(1 for rm in rooms if rm.status == 'Occupied')

    bills = []
    total_billing = 0.0
    for m in members:
        m_mess = sum(l.amount for l in messing_logs if l.member_id == m.id)
        m_room = sum((rm.days * rm.tariff) for rm in rooms if rm.member_id == m.id)
        tot = m.monthly_sub + m_mess + m_room
        total_billing += tot
        bills.append({
            'service_no': m.service_no,
            'officer_name': f"{m.rank} {m.name}",
            'sub': m.monthly_sub,
            'messing': m_mess,
            'room': m_room,
            'total': tot
        })

    return render_template(
        'officers-mess-app.html',
        members=members,
        rations=rations,
        messing_logs=messing_logs,
        rooms=rooms,
        audits=audits,
        low_stock_count=low_stock_count,
        total_messing=total_messing,
        occupied_rooms=occupied_rooms,
        bills=bills,
        total_billing=total_billing
    )

@app.route('/officers-mess/add-member', methods=['POST'])
def mess_add_member():
    m = MessMember(
        service_no=request.form.get('service_no'),
        rank=request.form.get('rank'),
        name=request.form.get('name'),
        living_status=request.form.get('living_status'),
        monthly_sub=float(request.form.get('monthly_sub') or 1500)
    )
    db.session.add(m)
    db.session.commit()
    log_mess_audit('Members', f"Added {m.rank} {m.name} ({m.service_no})")
    return redirect('/officers-mess/app')

@app.route('/officers-mess/delete-member/<int:mid>')
def mess_delete_member(mid):
    m = MessMember.query.get_or_404(mid)
    log_mess_audit('Members', f"Removed {m.rank} {m.name} ({m.service_no})")
    db.session.delete(m)
    db.session.commit()
    return redirect('/officers-mess/app')

@app.route('/officers-mess/add-ration', methods=['POST'])
def mess_add_ration():
    r = MessRation(
        category=request.form.get('category'),
        item_name=request.form.get('item_name'),
        unit=request.form.get('unit'),
        opening=float(request.form.get('opening') or 0),
        receipt=float(request.form.get('receipt') or 0),
        issued=float(request.form.get('issued') or 0),
        rate=float(request.form.get('rate') or 0),
        min_level=float(request.form.get('min_level') or 10)
    )
    db.session.add(r)
    db.session.commit()
    log_mess_audit('Ration', f"Updated {r.item_name} ({r.category})")
    return redirect('/officers-mess/app')

@app.route('/officers-mess/add-messing', methods=['POST'])
def mess_add_messing():
    mid = int(request.form.get('member_id'))
    m = MessMember.query.get(mid)
    officer_name = f"{m.rank} {m.name}" if m else "Unknown Officer"
    log = MessingLog(
        member_id=mid,
        officer_name=officer_name,
        meal_type=request.form.get('meal_type'),
        headcount=int(request.form.get('headcount') or 1),
        amount=float(request.form.get('amount') or 0),
        remarks=request.form.get('remarks') or ''
    )
    db.session.add(log)
    db.session.commit()
    log_mess_audit('Messing', f"{officer_name} - {log.meal_type}: ₹{log.amount}")
    return redirect('/officers-mess/app')

@app.route('/officers-mess/book-room', methods=['POST'])
def mess_book_room():
    mid = int(request.form.get('member_id'))
    m = MessMember.query.get(mid)
    officer_name = f"{m.rank} {m.name}" if m else "Unknown Officer"
    rm = MessGuestRoom(
        room_no=request.form.get('room_no'),
        member_id=mid,
        officer_name=officer_name,
        guest_name=request.form.get('guest_name'),
        days=int(request.form.get('days') or 1),
        tariff=float(request.form.get('tariff') or 800),
        status='Occupied'
    )
    db.session.add(rm)
    db.session.commit()
    log_mess_audit('Guest Room', f"Checked in {rm.guest_name} to Room {rm.room_no}")
    return redirect('/officers-mess/app')

@app.route('/officers-mess/checkout-room/<int:rid>')
def mess_checkout_room(rid):
    rm = MessGuestRoom.query.get_or_404(rid)
    rm.status = 'Checked Out'
    db.session.commit()
    log_mess_audit('Guest Room', f"Checked out {rm.guest_name} from Room {rm.room_no}")
    return redirect('/officers-mess/app')

@app.route('/officers-mess/export-csv')
def mess_export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Service No', 'Officer Name', 'Status', 'Base Subscription (INR)', 'Messing & EMC (INR)', 'Room Charges (INR)', 'Total Bill (INR)'])
    members = MessMember.query.all()
    messing_logs = MessingLog.query.all()
    rooms = MessGuestRoom.query.all()
    for m in members:
        m_mess = sum(l.amount for l in messing_logs if l.member_id == m.id)
        m_room = sum((rm.days * rm.tariff) for rm in rooms if rm.member_id == m.id)
        writer.writerow([m.service_no, f"{m.rank} {m.name}", m.living_status, m.monthly_sub, m_mess, m_room, m.monthly_sub + m_mess + m_room])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=officers_mess_billing_report.csv"})
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
