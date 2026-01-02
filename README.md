# Smart Nearby Places Recommendation System

# to activate virtual environment
.\myenv\Scripts\Activate


## Overview
An ML-powered location-based recommendation system that suggests nearby places
based on user mood, distance, ratings, time, and learned preferences.

## Tech Stack
- Python, Flask
- Scikit-learn, Pandas
- Google Places API
- React

## Features
- Location-based place discovery
- Feature engineering from raw API data
- ML model to predict place relevance
- Personalized recommendations

## ML Approach
- Supervised classification model
- Features: distance, rating, price, open status, user mood
- Model: Logistic Regression / Random Forest
- Metrics: Accuracy, Precision, ROC-AUC

## How to Run
### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
