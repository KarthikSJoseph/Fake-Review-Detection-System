# Fake Review Detection System

A Flask web application that classifies product reviews as **Fake** or **Genuine** using a 1D Convolutional Neural Network (TensorFlow/Keras). Reviews can be submitted as text, uploaded in bulk (CSV/Excel), or extracted from a screenshot with OCR. Reviews classified as genuine are also recorded in a simple proof-of-work hash-chained ledger.

## Features

- **User accounts** – registration, login and logout (Flask-Login, hashed passwords).
- **Single review analysis** – submit a review and get a label plus a confidence score.
- **Bulk analysis** – upload a CSV or Excel file (first column = review text).
- **Screenshot analysis** – upload an image; text is extracted with Tesseract OCR (`pytesseract` + OpenCV) and each line is classified.
- **Dashboard and history** – per-user totals of fake and genuine reviews, with a results page for each analysis.
- **Genuine-review ledger** – genuine reviews are appended to a blockchain-style ledger (SHA-256, proof-of-work), viewable at `/blockchain_table`.

## How it works

```
Review text
   │
   ├─ Rule-based pre-check ── fewer than 3 words, or contains a spam keyword/URL ──► Fake
   │
   └─ Preprocessing: lowercase → strip non-letters → tokenize → remove stopwords → Porter stem
          │
          ▼
   Keras Tokenizer → integer sequence → pad/truncate to 150 tokens
          │
          ▼
   1D CNN → sigmoid probability P(fake)
          │
          ▼
   P ≥ 0.5 → Fake (confidence = P)      P < 0.5 → Genuine (confidence = 1 − P)
```

### Model architecture

| Layer | Configuration |
|---|---|
| Embedding | 20,000-word vocabulary, 128 dimensions, input length 150 |
| Conv1D + BatchNorm | 256 filters, kernel 5, ReLU |
| Conv1D + BatchNorm | 128 filters, kernel 3, ReLU |
| Conv1D | 64 filters, kernel 3, ReLU |
| GlobalMaxPooling1D | – |
| Dropout | 0.5 |
| Dense | 128, ReLU |
| Dropout | 0.7 |
| Dense | 64, ReLU |
| Dense (output) | 1, sigmoid |

**Training setup** (`1dcnn_model.py`): Adam optimizer, binary cross-entropy, batch size 64, up to 20 epochs with early stopping on validation loss (patience 5, best weights restored), balanced class weights, 80/20 train/test split with `random_state=42`, and a further 20% of the training set used for validation.

### Dataset

`Fake_Reviews_Dataset1.csv` – about 41,000 labelled reviews, split almost evenly between the two classes (about 20,500 each). In the code, label `1` = fake and `0` = genuine.

### Evaluation

Results on the held-out 20% test split (8,193 reviews), produced by `python 1dcnn_model.py`:

| Class | Precision | Recall | F1-score | Support |
|---|---|---|---|---|
| 0 – Genuine | 0.89 | 0.83 | 0.86 | 4,013 |
| 1 – Fake | 0.85 | 0.90 | 0.87 | 4,180 |
| **Overall accuracy** | | | **0.87** (86.6%) | 8,193 |

Training stopped at epoch 11 through early stopping, and the weights from the best validation-loss epoch (epoch 6) were restored. The model overfits somewhat: training accuracy reaches about 97% while validation accuracy plateaus around 87%. Exact figures vary slightly from run to run.

## Tech stack

| Area | Technology |
|---|---|
| Backend | Python 3.10, Flask, Flask-Login, Flask-SQLAlchemy |
| Database | SQLite (via SQLAlchemy; the URI can be pointed at MySQL/PostgreSQL) |
| ML | TensorFlow / Keras (1D CNN), scikit-learn, NLTK |
| OCR / image | Tesseract, `pytesseract`, OpenCV |
| Data handling | pandas, openpyxl |
| Deployment | Gunicorn, Docker, Render |

## Project structure

```
├── app.py                  # Flask app: routes, auth, prediction pipeline
├── blockchain.py           # Proof-of-work hash-chained ledger
├── 1dcnn_model.py          # Training script (produces the two files in models/)
├── models/
│   ├── fake_review_model.h5
│   └── tokenizer.pkl
├── Fake_Reviews_Dataset1.csv
├── templates/              # Jinja2 templates
├── static/                 # CSS, JS, logo
├── requirements.txt
├── Dockerfile · Procfile · render.yaml · build.sh · runtime.txt
```

## Getting started

### Prerequisites
- Python 3.10
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed (Linux: `sudo apt install tesseract-ocr`; Windows: default install path `C:\Program Files\Tesseract-OCR\`)

### Run locally

```bash
git clone https://github.com/KarthikSJoseph/Fake-Review-Detection-System.git
cd Fake-Review-Detection-System

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

export SECRET_KEY="change-me"   # Windows (PowerShell): $env:SECRET_KEY="change-me"
python app.py
```

Open `http://127.0.0.1:10000`, register an account and log in. (The port comes from the `PORT` environment variable and defaults to 10000.) NLTK stopword and punkt data are downloaded automatically on first run.

### Retrain the model (optional)

```bash
python 1dcnn_model.py
```

This overwrites `models/fake_review_model.h5` and `models/tokenizer.pkl`.

### Docker

```bash
docker build -t fake-review-detector .
docker run -p 8000:8000 -e PORT=8000 -e SECRET_KEY=change-me fake-review-detector
```

Gunicorn binds to `0.0.0.0:$PORT` when `PORT` is set, which is why the variable is passed to the container.

## Routes

| Route | Method | Purpose |
|---|---|---|
| `/register`, `/login`, `/logout` | POST / GET | Authentication |
| `/dashboard` | GET | Per-user statistics and history |
| `/api/predict` | POST | Classify a single review (JSON response) |
| `/upload_csv` | POST | Classify a CSV of reviews |
| `/api/upload` | POST | Classify a CSV/Excel file; results saved to history |
| `/upload_image` | GET/POST | OCR a screenshot and classify each line |
| `/results/<id>` | GET | Detail page for one analysis |
| `/blockchain_table` | GET | View the genuine-review ledger |
| `/health` | GET | Health check |

## Known limitations

These are documented deliberately so the behaviour is clear:

- **Rule-based pre-filter.** Reviews shorter than 3 words, or containing keywords such as `http`, `www`, `free`, `offer`, `buy now` or `click here`, are labelled Fake without reaching the CNN. Genuine reviews that happen to contain those words can be misclassified.
- **Very short reviews.** The model was trained on full-length reviews; for inputs of only a few words its output is close to constant (about 0.57 in tests), which is why the short-review rule exists. Longer, realistic reviews are where its accuracy figures apply.
- **Model scope.** The model learns patterns from a single dataset; it classifies writing style, not whether a purchase really happened. Accuracy on reviews from other domains is untested.
- **Ledger is in-memory and shared.** The blockchain lives in application memory, so it resets when the server restarts, and it is one global ledger rather than one per user. Persisting it to the database is planned. Genuine reviews still remain in the SQL history table.
- **Ledger coverage.** `/api/upload` stores results in the database but does not append to the ledger, unlike the other prediction routes.
- **Proof-of-work cost.** Each genuine review mines a block (difficulty: hash starting with `0000`), so very large batches are slower.
- **SQLite on ephemeral hosts.** On platforms with non-persistent disks (e.g. Render's free tier), the SQLite file can be reset on redeploy.
- **Development-only route.** `/test_model` is a leftover debug route and should be removed before production use.
- **Configuration.** Set `SECRET_KEY` in the environment; the code falls back to a development key if it is missing.

## Future improvements

- Persist the ledger in the database and scope it per user.
- Replace keyword rules with a calibrated probability threshold, or a transformer-based model, and report metrics on an external dataset.
- Add automated tests and CI.
- Move to MySQL/PostgreSQL for deployment.

## Author

**Karthik S. Joseph** – B.Tech Computer Science and Engineering, SCMS College of Engineering and Technology
[GitHub](https://github.com/KarthikSJoseph) · [LinkedIn](https://linkedin.com/in/karthik-s-joseph)
