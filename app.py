import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
import tensorflow as tf
import numpy as np

# ----------------------
# App & DB Configuration
# ----------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# Database (SQLite for simplicity)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ----------------------
# Models
# ----------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

class ReviewAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    review_text = db.Column(db.Text)
    result = db.Column(db.String(20))  # "Fake" or "Genuine"

# ----------------------
# Login Loader
# ----------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------------------
# Routes
# ----------------------
@app.route("/")
@login_required
def dashboard():
    total_analyses = ReviewAnalysis.query.count()
    total_fake = ReviewAnalysis.query.filter_by(result="Fake").count()
    total_genuine = ReviewAnalysis.query.filter_by(result="Genuine").count()
    return render_template("dashboard.html", total_analyses=total_analyses,
                           total_fake=total_fake, total_genuine=total_genuine)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials"
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ----------------------
# API for Predictions
# ----------------------
# Dummy model for demonstration; replace with your real TensorFlow model
def predict_review(text):
    # Example: randomly label reviews (replace with your model)
    return np.random.choice(["Fake", "Genuine"])

@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    review = request.form.get("review")
    if not review:
        return jsonify({"error": "No review provided"}), 400
    result = predict_review(review)
    analysis = ReviewAnalysis(review_text=review, result=result)
    db.session.add(analysis)
    db.session.commit()
    return jsonify({"result": result, "analysis_id": analysis.id})

# ----------------------
# File Upload Routes
# ----------------------
@app.route("/upload_csv", methods=["POST"])
@login_required
def upload_csv():
    file = request.files.get("file")
    if file:
        # Process CSV here
        return redirect(url_for("dashboard"))
    return "No file uploaded", 400

@app.route("/upload_image", methods=["POST"])
@login_required
def upload_image():
    file = request.files.get("image")
    if file:
        # Process image here
        return redirect(url_for("dashboard"))
    return "No image uploaded", 400

# ----------------------
# Run App (Render Compatible)
# ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    db.create_all()  # Ensure tables exist
    app.run(host="0.0.0.0", port=port)