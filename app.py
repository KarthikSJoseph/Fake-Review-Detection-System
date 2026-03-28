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
import threading

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

# Force CPU to prevent GPU errors on Render
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

# -------------------- LOAD MODEL (LAZY) --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, 'models', 'fake_review_model.h5')
tokenizer_path = os.path.join(BASE_DIR, 'models', 'tokenizer.pkl')

model = None
tokenizer = None
MAX_LEN = 200
stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

def load_resources():
    global model, tokenizer
    if model is None:
        try:
            model = load_model(model_path, compile=False)
        except Exception as e:
            print(f"Error loading model: {e}")
    if tokenizer is None:
        try:
            with open(tokenizer_path, 'rb') as f:
                tokenizer = pickle.load(f)
        except Exception as e:
            print(f"Error loading tokenizer: {e}")

# Preload model in background thread (avoids Render timeout)
threading.Thread(target=load_resources).start()

# -------------------- TEXT PREPROCESS --------------------
def preprocess_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', '', text)
    words = text.split()
    words = [stemmer.stem(w) for w in words if w not in stop_words]
    return " ".join(words)

# -------------------- PREDICT --------------------
def predict_review(text):
    load_resources()  # lazy load

    if model is None or tokenizer is None:
        return 1, 0.0  # safe default if not loaded

    if len(text.split()) < 3:
        return 1, 0.90

    if re.search(r'(http|www|buy now|click here|free|offer)', text.lower()):
        return 1, 0.95

    clean = preprocess_text(text)
    seq = tokenizer.texts_to_sequences([clean])
    pad = pad_sequences(seq, maxlen=MAX_LEN)
    prob = float(model.predict(pad, verbose=0)[0][0])

    if prob > 0.5:
        return 1, prob
    else:
        return 0, 1 - prob

# -------------------- ROUTES --------------------
# ... keep all your existing routes unchanged ...
# index, login, register, dashboard, api_predict, upload_csv, upload_image, blockchain_table, logout
# -------------------- INIT DB --------------------
with app.app_context():
    db.create_all()