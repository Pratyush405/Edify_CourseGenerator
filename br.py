import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
import re

class BookRecommender:
    def __init__(self, data):
        """Initialize the recommender with book data"""
        self.df = pd.DataFrame(data)
   
        nltk.download('stopwords', quiet=True)
   
        self.df['processed_description'] = self.df['Description'].fillna('').apply(self.preprocess_text)

        self.tfidf = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.tfidf.fit_transform(self.df['processed_description'])
        
    def preprocess_text(self, text):
        """Clean and preprocess the text"""
        if not isinstance(text, str):
            return ''

        text = text.lower()
        
        text = re.sub(r'<.*?>', '', text)
        
        text = re.sub(r'[^a-zA-Z\s]', '', text)

        text = ' '.join(text.split())
        
        return text
    
    def get_recommendations(self, input_description, num_recommendations=5):
        """Get book recommendations based on input description"""

        processed_input = self.preprocess_text(input_description)
        
        input_vector = self.tfidf.transform([processed_input])
        
        similarity_scores = cosine_similarity(input_vector, self.tfidf_matrix).flatten()
        
        similar_indices = similarity_scores.argsort()[::-1][:num_recommendations]
        
        recommendations = []
        for idx in similar_indices:
            recommendations.append({
                'Name': self.df.iloc[idx]['Name'],
                'Authors': self.df.iloc[idx]['Authors'],
                'Description': self.df.iloc[idx]['Description'],
                'Rating': self.df.iloc[idx]['Rating'],
                'PublishYear': self.df.iloc[idx]['PublishYear'],
                'Similarity Score': similarity_scores[idx]
            })
        
        return recommendations

if __name__ == "__main__":
  
    df = pd.read_csv('./book1.csv')
    data = df.to_dict('records')

    recommender = BookRecommender(data)

    input_description = "A story about computers and artificial intelligence"
    recommendations = recommender.get_recommendations(input_description, num_recommendations=5)


    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['Name']}")
        print(f"Similarity Score: {rec['Similarity Score']:.2f}")


    

