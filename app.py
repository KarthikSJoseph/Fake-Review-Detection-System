from flask import Flask, render_template, request, jsonify
from keras.models import load_model
import numpy as np
import nltk
import pickle
import os

# Download NLTK stopwords (needed if preprocessing uses them)
nltk.download('stopwords')

app = Flask(__name__)

# -------------------------
# Load your trained model
# -------------------------
MODEL_PATH = os.path.join(os.getcwd(), "model.h5")

# Fix deserialization error by adding compile=False
model = load_model(MODEL_PATH, compile=False)

# Load vectorizer / tokenizer used for preprocessing
VECTORIZER_PATH = os.path.join(os.getcwd(), "vectorizer.pkl")
with open(VECTORIZER_PATH, "rb") as f:
    vectorizer = pickle.load(f)

# -------------------------
# Flask Routes
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    review = request.form.get("review")
    if not review:
        return jsonify({"error": "No review provided"}), 400

    # Transform review for model input
    review_vect = vectorizer.transform([review]).toarray()

    # Predict using the loaded model
    pred_prob = model.predict(review_vect)[0][0]

    # Classify review
    label = "Fake" if pred_prob > 0.5 else "Genuine"

    return jsonify({"prediction": label, "probability": float(pred_prob)})

# -------------------------
# Run the app
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Ensure Render can bind to the right port
    app.run(host="0.0.0.0", port=port)