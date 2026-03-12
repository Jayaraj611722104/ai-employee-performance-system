# ai_module/backend/ai_service.py
import joblib
import os
import pandas as pd
import numpy as np

# Load model and features
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml_models', 'performance_model.pkl')
FEATURES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml_models', 'features.joblib')

class AIService:
    def __init__(self):
        try:
            self.model = joblib.load(MODEL_PATH)
            self.feature_names = joblib.load(FEATURES_PATH)
            print("AI Service: Performance model loaded successfully.")
        except Exception as e:
            print(f"AI Service: Error loading model: {str(e)}")
            self.model = None

    def calculate_metrics(self, data):
        """
        Calculate metrics based on user requirements.
        data: dict with present_days, total_working_days, completed_tasks, assigned_tasks, bug_rate, rework_rate, peer_review_score
        """
        # 1. Attendance Analysis
        present = data.get('present_days', 0)
        total = data.get('total_working_days', 22)
        attendance_score = min(100, (present / total) * 100) if total > 0 else 0
        
        # 2. Task Productivity Analysis
        completed = data.get('completed_tasks', 0)
        assigned = data.get('assigned_tasks', 0)
        task_completion_rate = min(100, (completed / assigned) * 100) if assigned > 0 else 0
        
        # 3. Work Quality Analysis
        bug_rate = data.get('bug_rate', 0)
        rework_rate = data.get('rework_rate', 0)
        quality_score = max(0, 100 - bug_rate - rework_rate)
        
        # 4. Performance Review Analysis
        peer_review_score = data.get('peer_review_score', 0)
        
        # Productivity Score Calculation
        # 0.40 * task_completion_rate + 0.30 * attendance_score + 0.20 * quality_score + 0.10 * peer_review_score
        productivity_score = (0.40 * task_completion_rate + 
                              0.30 * attendance_score + 
                              0.20 * quality_score + 
                              0.10 * peer_review_score)
        
        return {
            'attendance_score': round(attendance_score, 2),
            'task_completion_rate': round(task_completion_rate, 2),
            'quality_score': round(quality_score, 2),
            'productivity_score': round(productivity_score, 2),
            'peer_review_score': round(peer_review_score, 2)
        }

    def predict_performance(self, metrics, manager_rating, experience_years):
        """
        Predict performance level using ML model.
        metrics: dict from calculate_metrics
        """
        if self.model is None:
            return "Error: Model not loaded", 0
        
        # Prepare input data in correct order
        # FEATURES: attendance_score, task_completion_rate, quality_score, productivity_score, peer_review_score, manager_rating, years_of_experience
        input_data = pd.DataFrame([{
            'attendance_score': metrics['attendance_score'],
            'task_completion_rate': metrics['task_completion_rate'],
            'quality_score': metrics['quality_score'],
            'productivity_score': metrics['productivity_score'],
            'peer_review_score': metrics['peer_review_score'],
            'manager_rating': manager_rating,
            'years_of_experience': experience_years
        }])
        
        # Reorder columns to match model training
        input_data = input_data[self.feature_names]
        
        prediction = self.model.predict(input_data)[0]
        probabilities = self.model.predict_proba(input_data)[0]
        max_prob = round(float(np.max(probabilities)) * 100, 2)
        
        return prediction, max_prob

    def get_promotion_recommendation(self, performance_score, attendance_score, experience_years, manager_rating):
        """
        Promotion Recommendation Logic based on user criteria.
        """
        # performance_score > 85, attendance_score > 90, experience_years > 2, manager_rating >= 4
        if (performance_score > 85 and 
            attendance_score > 90 and 
            experience_years > 2 and 
            manager_rating >= 4):
            return "Recommended"
        else:
            return "Not Recommended"

# Initialize global service
ai_service = AIService()
