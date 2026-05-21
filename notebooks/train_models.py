import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# Ensure the parent directory is in the path so we can import from backend.app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.preprocess import preprocess_text

def train_and_evaluate():
    print("--- Starting Email Spam Detection Model Training ---")
    
    # 1. Load Dataset
    dataset_path = os.path.join("dataset", "spam_or_not_spam.csv")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}. Please download it first.")
        
    print(f"Loading dataset from: {dataset_path}")
    df = pd.read_csv(dataset_path)
    print(f"Initial shape: {df.shape}")
    print("Columns:", list(df.columns))
    
    # 2. Data Cleaning
    # Check for missing values
    missing_count = df.isnull().sum().sum()
    if missing_count > 0:
        print(f"Found {missing_count} missing values. Handling by dropping rows...")
        df.dropna(inplace=True)
        
    # Check for duplicate records
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        print(f"Found {duplicate_count} duplicate rows. Handling by dropping duplicates...")
        df.drop_duplicates(inplace=True)
        
    print(f"Cleaned dataset shape: {df.shape}")
    print("Label distribution:")
    print(df['label'].value_counts(normalize=True))
    
    # 3. NLP Preprocessing
    print("Preprocessing email text... (This may take a minute)")
    # Apply our modular preprocessor
    df['processed_text'] = df['email'].apply(preprocess_text)
    
    # Remove any rows that became empty after preprocessing
    empty_preprocessed = df[df['processed_text'] == ""]
    if len(empty_preprocessed) > 0:
        print(f"Dropping {len(empty_preprocessed)} rows that became empty after text preprocessing.")
        df = df[df['processed_text'] != ""]
        
    print(f"Final training dataset shape: {df.shape}")
    
    # 4. Feature Engineering
    print("Extracting TF-IDF features...")
    # Limit max_features to avoid overfitting and keep serialized size small
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    
    # Split dataset into training and testing sets (80% train, 20% test)
    X = df['processed_text']
    y = df['label']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Train set size: {X_train.shape[0]}")
    print(f"Test set size: {X_test.shape[0]}")
    
    X_train_vectorized = vectorizer.fit_transform(X_train)
    X_test_vectorized = vectorizer.transform(X_test)
    
    # 5. Model Building & Training
    nb_model = MultinomialNB()
    lr_model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
    svm_model = SVC(kernel='linear', probability=True, class_weight='balanced', random_state=42)
    
    models = {
        "Naive Bayes": nb_model,
        "Logistic Regression": lr_model,
        "Support Vector Machine": svm_model,
        "Ensemble Model": VotingClassifier(
            estimators=[
                ('nb', nb_model),
                ('lr', lr_model),
                ('svm', svm_model)
            ],
            voting='soft'
        )
    }
    
    metrics_summary = {}
    
    # Create model output directory
    os.makedirs("model", exist_ok=True)
    
    for name, model in models.items():
        print(f"Training {name} model...")
        model.fit(X_train_vectorized, y_train)
        
        # Predictions
        y_pred = model.predict(X_test_vectorized)
        
        # Calculate Metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred)
        
        print(f"[{name}] Results:")
        print(f"  Accuracy : {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall   : {recall:.4f}")
        print(f"  F1-Score : {f1:.4f}")
        
        # Save metrics
        metrics_summary[name] = {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "confusion_matrix": cm.tolist() # [[tn, fp], [fn, tp]]
        }
        
        # Generate and save Confusion Matrix Plot
        plt.figure(figsize=(5, 4))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=['Not Spam', 'Spam'],
                    yticklabels=['Not Spam', 'Spam'])
        plt.title(f'Confusion Matrix - {name}')
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        plt.tight_layout()
        cm_filename = os.path.join("model", f"confusion_matrix_{name.lower().replace(' ', '_')}.png")
        plt.savefig(cm_filename, dpi=150)
        plt.close()
        print(f"  Saved confusion matrix plot to {cm_filename}")
        
        # Save trained model
        model_filename = os.path.join("model", f"{name.lower().replace(' ', '_')}_model.pkl")
        joblib.dump(model, model_filename)
        print(f"  Saved trained model to {model_filename}")
        
    # Save the TF-IDF Vectorizer
    vectorizer_filename = os.path.join("model", "tfidf_vectorizer.pkl")
    joblib.dump(vectorizer, vectorizer_filename)
    print(f"Saved TF-IDF Vectorizer to {vectorizer_filename}")
    
    # Save metrics JSON for backend API consumption
    metrics_json_path = os.path.join("model", "metrics_comparison.json")
    with open(metrics_json_path, 'w') as f:
        json.dump(metrics_summary, f, indent=4)
    print(f"Saved model comparison metrics to {metrics_json_path}")
    
    # 6. Plot model comparison charts
    print("Generating model comparison chart...")
    categories = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    
    x = np.arange(len(categories))
    width = 0.2
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract values for plotting
    nb_vals = [metrics_summary["Naive Bayes"]["accuracy"], metrics_summary["Naive Bayes"]["precision"],
               metrics_summary["Naive Bayes"]["recall"], metrics_summary["Naive Bayes"]["f1_score"]]
    lr_vals = [metrics_summary["Logistic Regression"]["accuracy"], metrics_summary["Logistic Regression"]["precision"],
               metrics_summary["Logistic Regression"]["recall"], metrics_summary["Logistic Regression"]["f1_score"]]
    svm_vals = [metrics_summary["Support Vector Machine"]["accuracy"], metrics_summary["Support Vector Machine"]["precision"],
                metrics_summary["Support Vector Machine"]["recall"], metrics_summary["Support Vector Machine"]["f1_score"]]
    ens_vals = [metrics_summary["Ensemble Model"]["accuracy"], metrics_summary["Ensemble Model"]["precision"],
                metrics_summary["Ensemble Model"]["recall"], metrics_summary["Ensemble Model"]["f1_score"]]
    
    ax.bar(x - 1.5 * width, nb_vals, width, label='Naive Bayes', color='#3b82f6') # Blue
    ax.bar(x - 0.5 * width, lr_vals, width, label='Logistic Regression', color='#10b981') # Green
    ax.bar(x + 0.5 * width, svm_vals, width, label='Support Vector Machine', color='#8b5cf6') # Purple
    ax.bar(x + 1.5 * width, ens_vals, width, label='Ensemble Model', color='#f59e0b') # Orange
    
    ax.set_ylabel('Scores')
    ax.set_title('Model Performance Metrics Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylim(0.8, 1.02) # Standardize axis to highlight differences
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    comparison_filename = os.path.join("model", "metrics_comparison.png")
    plt.savefig(comparison_filename, dpi=150)
    plt.close()
    print(f"Saved model performance comparison graph to {comparison_filename}")
    
    print("\n--- Training Pipeline Successfully Completed ---")

if __name__ == "__main__":
    train_and_evaluate()
