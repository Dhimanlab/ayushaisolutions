import os
import io
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from pypdf import PdfReader

app = Flask(__name__)
CORS(app)

# Configure the classic Google AI engine using your secure environment variable
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# Global memory holder for your active PDF text string
document_context = ""

# ----------------- WEBSITE PAGE ROUTING -----------------

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except:
        return render_template('login.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

# ----------------- EXPERIMENTAL AI WORKFLOWS -----------------

# ROUTE 1: PDF Text Extraction and Analysis
@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    global document_context
    if 'pdf' not in request.files:
        return jsonify({"error": "No file uploaded. Please select a valid PDF file."}), 400
        
    file = request.files['pdf']
    if file.filename == '':
        return jsonify({"error": "No file selected."}), 400
        
    try:
        # Stream file binary text directly into structural string format
        pdf_stream = io.BytesIO(file.read())
        reader = PdfReader(pdf_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
            
        document_context = text

        # Free tier limitation check (prevents massive payload processing)
        if len(document_context) > 12000:
            return jsonify({"error": "This document exceeds the limit for the Free Tier. Please upgrade to Premium!"}), 403

        if not document_context.strip():
            return jsonify({"error": "Could not extract text from this PDF. Ensure it's not a scanned image."}), 400

        # Execute generation request using the classic generativeai module model
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"Summarize this text concisely using structured bullet points:\n\n{document_context}"
        )
        return jsonify({"summary": response.text})
        
    except Exception as e:
        print(f"Server Error during PDF parsing: {e}")
        return jsonify({"error": "Unable to complete document analysis."}), 500

# ROUTE 2: Interactive Query Interface
@app.route('/api/chat', methods=['POST'])
def chat_pdf():
    global document_context
    if not document_context:
        return jsonify({"error": "Please upload a document workspace first before starting a chat."}), 400
        
    data = request.json or {}
    question = data.get('question')
    if not question:
        return jsonify({"error": "Question parameter is empty."}), 400
    
    try:
        # Prompt configuration forces Gemini to only look inside your uploaded PDF
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"Context Document:\n{document_context}\n\nQuestion: {question}\nAnswer the question strictly based on the text provided above."
        )
        return jsonify({"answer": response.text})
    except Exception as e:
        print(f"Server Error during AI generation: {e}")
        return jsonify({"error": "AI provider service connection failed."}), 500

# ----------------- EXECUTION SYSTEM ENGINE -----------------
if __name__ == '__main__':
    port_config = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port_config, debug=False)
