import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Set writable NLTK data directory for serverless environments (like Vercel)
import os
nltk_data_dir = os.path.join("/tmp", "nltk_data")
os.makedirs(nltk_data_dir, exist_ok=True)
if nltk_data_dir not in nltk.data.path:
    nltk.data.path.append(nltk_data_dir)

# Initialize NLTK resources dynamically
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", download_dir=nltk_data_dir, quiet=True)

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", download_dir=nltk_data_dir, quiet=True)

try:
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("wordnet", download_dir=nltk_data_dir, quiet=True)

try:
    nltk.data.find("corpora/omw-1.4")
except LookupError:
    nltk.download("omw-1.4", download_dir=nltk_data_dir, quiet=True)

# Set of stopwords
STOPWORDS = set(stopwords.words("english"))
LEMMATIZER = WordNetLemmatizer()

def clean_text(text: str) -> str:
    """
    Cleans raw text by removing HTML tags, URLs, email addresses,
    punctuation, and special characters.
    """
    if not isinstance(text, str):
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Remove URLs -> Replace with 'url'
    text = re.sub(r"https?://\S+|www\.\S+", " url ", text)
    
    # Remove Email addresses -> Replace with 'email'
    text = re.sub(r"\S+@\S+", " email ", text)
    
    # Remove HTML tags -> Replace with space
    text = re.sub(r"<.*?>", " ", text)
    
    # Remove numbers -> Replace with 'number'
    text = re.sub(r"\d+", " number ", text)
    
    # Remove punctuation
    # We replace punctuation with space to avoid merging words (e.g. "word.another" -> "word another")
    translator = str.maketrans(string.punctuation, " " * len(string.punctuation))
    text = text.translate(translator)
    
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    
    return text

def preprocess_text(text: str) -> str:
    """
    Complete NLP preprocessing pipeline: cleaning, tokenization,
    stopword removal, and lemmatization.
    """
    # 1. Clean the text
    cleaned = clean_text(text)
    
    if not cleaned:
        return ""
    
    # 2. Tokenize
    try:
        tokens = word_tokenize(cleaned)
    except Exception:
        # Fallback tokenize if NLTK fails for some reason
        tokens = cleaned.split()
        
    # 3. Stopwords removal and Lemmatization
    processed_tokens = []
    for token in tokens:
        if token not in STOPWORDS and len(token) > 1:
            # Lemmatize
            lemma = LEMMATIZER.lemmatize(token)
            processed_tokens.append(lemma)
            
    # 4. Join back into a single string
    return " ".join(processed_tokens)
