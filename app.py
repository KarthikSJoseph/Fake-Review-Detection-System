import os
import re
import json
import time
import hashlib
import pickle
import numpy as np
import pandas as pd
import pytesseract
import cv2
import nltk
import tensorflow as tf

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from datetime import datetime

# -------------------- BASIC SETUP --------------------
nltk.download('stopwords')
tf.config.set_visible_devices([], 'GPU')

# -------------------- FLASK SETUP --------------------
app = Flask(__name__)
app.secret_key = "secret123"

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# -------------------- TESSERACT --------------------
try:
    pytesseract.get_tesseract_version()
except:
    pytesseract.pytesseract.tesseract_cmd = None

# -------------------- BLOCKCHAIN --------------------
class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_block(previous_hash='0')

    def create_block(self, data=None, previous_hash=''):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(time.time()),
            'data': data,
            'previous_hash': previous_hash
        }
        block['hash'] = self.hash(block)
        self.chain.append(block)
        return block

    def add_review(self, data):
        previous_hash = self.chain[-1]['hash']
        self.create_block(data, previous_hash)

    def hash(self, block):
        encoded = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

blockchain = Blockchain()

# -------------------- DATABASE MODELS --------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(200))

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    review = db.Column(db.Text)
    result = db.Column(db.Integer)
    confidence = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------- LOAD MODEL --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, 'models', 'fake_review_model.h5')
tokenizer_path = os.path.join(BASE_DIR, 'models', 'tokenizer.pkl')

model, tokenizer = None, None

def load_resources():
    global model, tokenizer
    if model is None:
        model = load_model(model_path, compile=False)
    if tokenizer is None:
        with open(tokenizer_path, 'rb') as f:
            tokenizer = pickle.load(f)

MAX_LEN = 200
stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

# -------------------- TEXT PREPROCESS --------------------
def preprocess_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', '', text)
    words = text.split()
    words = [stemmer.stem(w) for w in words if w not in stop_words]
    return " ".join(words)

# -------------------- PREDICTION --------------------
def predict_review(text):
    load_resources()

    if len(text.split()) < 3:
        return 1, 0.90

    if re.search(r'(http|www|buy now|click here|free|offer)', text.lower()):
        return 1, 0.95

    clean = preprocess_text(text)
    seq = tokenizer.texts_to_sequences([clean])
    pad = pad_sequences(seq, maxlen=MAX_LEN)

    prob = float(model.predict(pad, verbose=0)[0][0])

    return (1, prob) if prob > 0.5 else (0, 1 - prob)

# -------------------- ROUTES --------------------
@app.route('/')
def index():
    return redirect(url_for('login'))

# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password")

    return render_template('login.html')

# -------- REGISTER --------
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    confirm = request.form['confirm_password']

    if password != confirm:
        flash("Passwords do not match")
        return redirect(url_for('login'))

    if User.query.filter_by(username=username).first():
        flash("Username already exists")
        return redirect(url_for('login'))

    new_user = User(username=username, password=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()

    flash("Account created successfully!")
    return redirect(url_for('login'))

# -------- DASHBOARD --------
@app.route('/dashboard')
@login_required
def dashboard():
    analyses = Analysis.query.filter_by(user_id=current_user.id).all()

    total_fake = sum(1 for a in analyses if a.result == 1)
    total_genuine = sum(1 for a in analyses if a.result == 0)
    total_analyses = len(analyses)

    return render_template(
        'dashboard.html',
        total_fake=total_fake,
        total_genuine=total_genuine,
        total_analyses=total_analyses
    )

# -------- API PREDICT --------
@app.route('/api/predict', methods=['POST'])
@login_required
def api_predict():
    review = request.form.get('review')

    if not review:
        return jsonify({"error": "No review provided"}), 400

    prediction, confidence = predict_review(review)

    analysis = Analysis(
        user_id=current_user.id,
        review=review,
        result=prediction,
        confidence=confidence
    )

    db.session.add(analysis)
    db.session.commit()

    if prediction == 0:
        blockchain.add_review({
            "review": review,
            "confidence": round(confidence * 100, 2),
            "user": current_user.username,
            "source": "Manual"
        })

    return jsonify({
        "result": "Fake" if prediction == 1 else "Genuine",
        "confidence": round(confidence * 100, 2),
        "analysis_id": analysis.id
    })

# -------- SINGLE RESULT PAGE --------
@app.route('/results/<int:analysis_id>')
@login_required
def results_page(analysis_id):
    analysis = Analysis.query.get_or_404(analysis_id)

    return render_template(
        'result_single.html',
        review=analysis.review,
        result="Fake" if analysis.result else "Genuine",
        confidence=round(analysis.confidence * 100, 2)
    )

# -------- CSV UPLOAD --------
@app.route('/upload_csv', methods=['POST'])
@login_required
def upload_csv():
    file = request.files.get('file')

    if not file:
        return "No file uploaded", 400

    df = pd.read_csv(file)
    results = []

    for review in df.iloc[:, 0]:
        review = str(review).strip()
        if not review:
            continue

        prediction, confidence = predict_review(review)

        if prediction == 0:
            blockchain.add_review({
                "review": review,
                "confidence": round(confidence * 100, 2),
                "user": current_user.username,
                "source": "CSV"
            })

        results.append({
            "review": review,
            "result": "Fake" if prediction else "Genuine",
            "confidence": round(confidence * 100, 2)
        })

    return render_template("results_bulk.html", results=results)

# -------- IMAGE UPLOAD --------
@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    file = request.files.get('image')

    if not file:
        return "No image uploaded", 400

    path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(path)

    try:
        img = cv2.imread(path)
        text = pytesseract.image_to_string(img)
    except Exception as e:
        print("OCR Error:", e)
        text = ""

    reviews = text.split('\n')
    results = []

    for review in reviews:
        review = review.strip()
        if not review:
            continue

        prediction, confidence = predict_review(review)

        if prediction == 0:
            blockchain.add_review({
                "review": review,
                "confidence": round(confidence * 100, 2),
                "user": current_user.username,
                "source": "Screenshot"
            })

        results.append({
            "review": review,
            "result": "Fake" if prediction else "Genuine",
            "confidence": round(confidence * 100, 2)
        })

    return render_template("results_bulk.html", results=results)

# -------- BLOCKCHAIN --------
@app.route('/blockchain_table')
@login_required
def blockchain_table():
    return render_template('blockchain_table.html', chain=blockchain.chain)

# -------- LOGOUT --------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# -------------------- INIT DB --------------------
with app.app_context():
    db.create_all()

# -------------------- RUN --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)