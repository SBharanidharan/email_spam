# ShieldMail AI - Email Spam Detection Dashboard

ShieldMail AI is a complete, production-ready machine learning project that classifies emails as **Spam** or **Ham (Not Spam)**. It features an interactive single-page web dashboard with light/dark theme modes, a real-time prediction playground, and a comparative performance analytics dashboard.

The application leverages three trained classifiers—**Multinomial Naive Bayes**, **Logistic Regression**, and a **Support Vector Machine (SVM)**—to process emails, extract TF-IDF word features, and make predictions.

---

## 📂 Project Structure

```text
email-detect/
│
├── dataset/
│   └── spam_or_not_spam.csv         # Labeled email dataset (3,000 samples)
│
├── notebooks/
│   ├── train_models.py              # Modular training & evaluation pipeline script
│   └── spam_detection_training.ipynb# Interactive Jupyter Notebook version
│
├── model/
│   ├── tfidf_vectorizer.pkl         # Serialized TF-IDF feature extractor
│   ├── naive_bayes_model.pkl        # Serialized Naive Bayes model
│   ├── logistic_regression_model.pkl# Serialized Logistic Regression model
│   ├── support_vector_machine_model.pkl # Serialized SVM model
│   ├── metrics_comparison.json      # Evaluation metrics (Accuracy, Precision, etc.)
│   └── metrics_comparison.png       # Performance evaluation chart
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI server (Predictor & static file server)
│   │   └── preprocess.py            # NLP Text Preprocessor (shared module)
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_api.py              # Pytest unit tests for FastAPI endpoints
│   ├── requirements.txt             # Python dependencies
│   └── run.py                       # Helper script to start uvicorn
│
├── frontend/
│   ├── index.html                   # Dashboard HTML UI structure
│   ├── style.css                    # Responsive dark/light theme CSS stylesheet
│   └── app.js                       # Frontend reactive logic & Chart.js rendering
│
├── README.md                        # Master Documentation
├── requirements.txt                 # Master python requirements list
└── setup_and_run.bat                # Automation script to install and launch the app
```

---

## ⚡ Quick Start (Windows)

The simplest way to install requirements, train the models, and launch the application on Windows is using the automated batch script:

1. Double-click the **`setup_and_run.bat`** file in the root folder.
2. The script will:
   - Verify Python is installed.
   - Install required dependencies via `pip`.
   - Train the ML models if they are not already present in the `model/` folder.
   - Launch your web browser to `http://127.0.0.1:8000/`.
   - Start the FastAPI backend server.

---

## 🛠️ Manual Installation & Running

If you prefer to run commands manually, follow these steps:

### 1. Install Dependencies
Ensure you have Python 3.10+ installed. Install the Python packages:
```bash
pip install -r requirements.txt
```

### 2. Train Models
Run the training pipeline script. This processes the raw email dataset, trains all three classifiers, calculates evaluation metrics, and saves the serialized weights.
```bash
python notebooks/train_models.py
```
*(Optional)* You can open the Jupyter Notebook at `notebooks/spam_detection_training.ipynb` to view interactive training outputs.

### 3. Run Unit Tests
Run backend tests to verify API endpoints, validation logic, and models are behaving correctly:
```bash
pytest backend/tests/test_api.py
```

### 4. Start the Application
Start the FastAPI server:
```bash
python backend/run.py
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your web browser to access the dashboard.

---

## 🧠 Machine Learning Pipeline

### 1. NLP Preprocessing
Before feeding raw email text into the models, the text goes through a strict preprocessing pipeline:
- **Lowercasing**: Standardizes casing.
- **Cleaning**: Removes HTML tags, email addresses, URLs, and numeric values using regular expressions.
- **Tokenization**: Splits sentences into individual word tokens.
- **Stopwords Removal**: Filters out common words (e.g., 'and', 'the', 'is') using the NLTK corpus.
- **Lemmatization**: Reduces words to their dictionary root form (e.g., 'running' -> 'run', 'studies' -> 'study') using `WordNetLemmatizer`.

### 2. Feature Extraction
The cleaned text is vectorized using a **TF-IDF Vectorizer** (Term Frequency-Inverse Document Frequency) restricted to **5,000 maximum features** and a word **n-gram range of (1, 2)** to capture word pairs.

### 3. Classifiers & Evaluation
We trained three models using an **80/20 train-test split** stratified by class labels. Performance comparison results on the test set:

| Model | Accuracy | Precision | Recall | F1-Score | Best For |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Support Vector Machine (Linear)** | **98.43%** | **100.00%** | **89.41%** | **94.41%** | **Highest overall performance (Recommended)** |
| **Naive Bayes (Multinomial)** | 96.52% | 98.51% | 77.65% | 86.84% | Simple, fast baseline text classifier |
| **Logistic Regression** | 96.17% | 100.00% | 74.12% | 85.14% | Strong linear classification baseline |

*Note: Precision is 100% for SVM and Logistic Regression on this test set, meaning 0 false positives occurred (no legitimate emails were classified as spam).*

---

## 🔌 API Documentation

FastAPI auto-generates interactive Swagger documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 1. Predict Spam Status
Classifies an email and returns the prediction and probability metrics.

- **Endpoint**: `POST /api/predict`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "text": "Dear customer, your online access is suspended. Please click here immediately to reset your passcode.",
    "model_name": "Support Vector Machine"
  }
  ```
- **Response**:
  ```json
  {
    "prediction": "Spam",
    "label": 1,
    "probability": 0.9996767759885816,
    "confidence": 0.9996767759885816,
    "model_used": "Support Vector Machine",
    "processed_text": "dear customer online access suspend please click immediately reset passcode"
  }
  ```

### 2. Get Evaluation Metrics
Retrieves comparison evaluation metrics and confusion matrices for dashboard charts.

- **Endpoint**: `GET /api/metrics`
- **Response**:
  ```json
  {
    "Naive Bayes": {
      "accuracy": 0.9652,
      "precision": 0.9851,
      "recall": 0.7765,
      "f1_score": 0.8684,
      "confusion_matrix": [[483, 7], [19, 66]]
    },
    ...
  }
  ```

---

## 🚀 Deployment Instructions

Because the application is structured with the FastAPI backend serving the HTML frontend assets, you can deploy the entire application as a **single unified service** or **split them apart**.

### Option A: Unified Service Deployment (Recommended)
You can deploy the entire repository directly to **Render** or **Railway**.

#### Deploying on Render:
1. Push this repository to GitHub.
2. Sign in to [Render](https://render.com/) and create a new **Web Service**.
3. Link your GitHub repository.
4. Set the following configurations:
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt && python notebooks/train_models.py`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
5. Click **Deploy**. Render will install dependencies, train the models, and run the service.

#### Deploying on Railway:
1. Create a new project on [Railway](https://railway.app/).
2. Link your GitHub repository.
3. Railway automatically detects Python and will read `requirements.txt`.
4. In your service **Variables**, set:
   - `PORT`: `8000` (FastAPI reads this or binds automatically)
5. In **Settings**, set the **Build Command** to: `pip install -r requirements.txt && python notebooks/train_models.py` and **Start Command** to: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`.

---

### Option B: Separate Frontend and Backend Deployment
If you want to host the frontend statically on **Vercel** or **Netlify**, and host the backend on **Render/Railway**:

#### 1. Backend (Render / Railway):
- Deploy the backend project as described above (you don't need to mount the static files folder, though it won't hurt).
- Note down your backend URL (e.g. `https://my-spam-api.onrender.com`).

#### 2. Frontend (Vercel / Netlify):
- Open `frontend/app.js` and change the API fetch URL:
  ```javascript
  // Replace:
  const response = await fetch("/api/predict", { ... })
  // With:
  const response = await fetch("https://my-spam-api.onrender.com/api/predict", { ... })
  ```
  *(Make sure to do the same for the `/api/metrics` endpoint in `loadAnalyticsDashboard`)*
- Deploy the contents of the `frontend/` directory to Vercel/Netlify as a static site.
- Enable CORS in the backend `main.py` by adding the frontend URL to the `allow_origins` list inside CORS middleware.

---

## 🔮 Future Improvements

1. **Active Learning Feedback Loop**: Add a button on the UI allowing users to flag incorrect predictions, saving these samples to retrain the models periodically.
2. **Deep Learning Classifiers**: Implement an LSTM model using PyTorch or fine-tune a pre-trained Transformer (e.g., DistilBERT) to capture deeper semantic relationships.
3. **Email Header Analysis**: Support uploading `.eml` files and parse header domains, SPF/DKIM records, and sender reputation for increased security.
4. **API Rate Limiting**: Apply FastAPI rate limiters to protect the prediction endpoint from spam requests.
