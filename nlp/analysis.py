from textblob import TextBlob
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except nltk.downloader.DownloadError:
    pass

def analyze_text(text):
    """
    Analyzes text to determine mood using both TextBlob and VADER.
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity

    sia = SentimentIntensityAnalyzer()
    vader_score = sia.polarity_scores(text)

    # Use a threshold on TextBlob's polarity for mood classification
    mood = 'positive' if polarity > 0.2 else 'negative' if polarity < -0.2 else 'neutral'
    
    # Return a dictionary with detailed analysis results
    return {'polarity': polarity, 'vader': vader_score, 'mood': mood}
