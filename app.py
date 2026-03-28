import os
from flask import Flask, render_template, request
from tensorflow.keras.models import load_model
import pickle
import numpy as np
import nltk
from nltk.corpus import stopwords
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Download stopwords once
nltk.download('stopwords')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Load trained model and tokenizer
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'fake_review_model.h5')
TOKENIZER_PATH = os.path.join(os.path.dirname(__file__), 'models', 'tokenizer.pkl')

model = load_model(MODEL_PATH)
with open(TOKENIZER_PATH, 'rb') as f:
    tokenizer = pickle.load(f)

stop_words = set(stopwords.words('english'))

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Prediction route
@app.route('/predict', methods=['POST'])
def predict():
    review_text = request.form['review']

    # Basic preprocessing: lowercase + remove stopwords
    words = [w for w in review_text.lower().split() if w not in stop_words]
    seq = tokenizer.texts_to_sequences([' '.join(words)])
    seq_padded = pad_sequences(seq, maxlen=100)  # Match your model's maxlen

    # Predict
    pred = model.predict(seq_padded)
    result = 'Fake' if pred[0][0] > 0.5 else 'Genuine'

    return render_template('result.html', review=review_text, prediction=result)

# Run app with Render-compatible port
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render sets PORT dynamically
    app.run(host='0.0.0.0', port=port, debug=True)