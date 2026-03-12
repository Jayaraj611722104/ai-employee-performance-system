# ai_module/ml_models/train_model.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

def generate_synthetic_data(num_samples=1000):
    np.random.seed(42)
    
    # Input Features
    attendance_score = np.random.uniform(70, 100, num_samples)
    task_completion_rate = np.random.uniform(60, 100, num_samples)
    quality_score = np.random.uniform(65, 100, num_samples)
    peer_review_score = np.random.uniform(60, 100, num_samples)
    manager_rating = np.random.randint(1, 6, num_samples)
    years_of_experience = np.random.randint(0, 15, num_samples)
    
    # Calculate weighted productivity_score based on user formula
    # productivity_score = 0.40 * task_completion_rate + 0.30 * attendance_score + 0.20 * quality_score + 0.10 * peer_review_score
    productivity_score = (0.40 * task_completion_rate + 
                          0.30 * attendance_score + 
                          0.20 * quality_score + 
                          0.10 * peer_review_score)
    
    # Define Target: Performance Level
    # Categories: Excellent, Good, Average, Needs Improvement
    performance_level = []
    for i in range(num_samples):
        score = productivity_score[i]
        m_rating = manager_rating[i]
        
        if score > 85 and m_rating >= 4:
            performance_level.append('Excellent')
        elif score > 75 and m_rating >= 3:
            performance_level.append('Good')
        elif score > 65:
            performance_level.append('Average')
        else:
            performance_level.append('Needs Improvement')
            
    data = pd.DataFrame({
        'attendance_score': attendance_score,
        'task_completion_rate': task_completion_rate,
        'quality_score': quality_score,
        'productivity_score': productivity_score,
        'peer_review_score': peer_review_score,
        'manager_rating': manager_rating,
        'years_of_experience': years_of_experience,
        'performance_level': performance_level
    })
    
    return data

def train_and_save():
    print("Generating synthetic data for training...")
    data = generate_synthetic_data(2000)
    
    X = data.drop('performance_level', axis=1)
    y = data['performance_level']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training RandomForestClassifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    print(f"Model Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save the model
    model_path = os.path.join(os.path.dirname(__file__), 'performance_model.pkl')
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")
    
    # Also save feature names
    features_path = os.path.join(os.path.dirname(__file__), 'features.joblib')
    joblib.dump(list(X.columns), features_path)
    print(f"Feature names saved to {features_path}")

if __name__ == "__main__":
    train_and_save()
