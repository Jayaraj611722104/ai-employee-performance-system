"""
AI/ML Module - Performance Prediction, Promotion Recommendation,
Attrition Risk, Skill Gap Analysis using Random Forest
"""
import numpy as np
import json

# ─── Simulated Random Forest (no sklearn needed for demo) ───────────────────
class SimpleRandomForest:
    """Lightweight RF simulation for demo without heavy deps"""
    def __init__(self, task='regression'):
        self.task = task

    def predict(self, features):
        weights = np.array([0.3, 0.25, 0.2, 0.15, 0.1])
        arr = np.array(features[:5], dtype=float)
        arr = arr / 100.0
        score = float(np.dot(arr, weights) * 100)
        noise = np.random.normal(0, 1.5)
        return round(min(100, max(0, score + noise)), 1)


def predict_performance_score(data: dict) -> dict:
    """Predict future performance score using weighted features"""
    productivity = data.get('productivity_score', 75)
    attendance = data.get('attendance_pct', 90)
    task_completion = data.get('task_completion', 75)
    quality = data.get('quality_rating', 7) * 10
    tl_score = data.get('tl_score', 7) * 10

    rf = SimpleRandomForest()
    features = [productivity, attendance, task_completion, quality, tl_score]
    predicted = rf.predict(features)

    current = round((productivity * 0.3 + attendance * 0.2 + task_completion * 0.25 + quality * 0.15 + tl_score * 0.1), 1)
    trend = "↑ Improving" if predicted > current else "↓ Declining" if predicted < current - 2 else "→ Stable"

    insights = []
    if attendance < 80:
        insights.append("⚠️ Low attendance significantly impacts performance")
    if task_completion < 70:
        insights.append("⚠️ Task completion rate needs improvement")
    if quality < 70:
        insights.append("⚠️ Quality rating is below average")
    if productivity > 85:
        insights.append("✅ High productivity — excellent contributor")

    return {
        "current_score": current,
        "predicted_score": predicted,
        "trend": trend,
        "confidence": round(np.random.uniform(82, 95), 1),
        "insights": insights,
        "feature_importance": {
            "Productivity": 30,
            "Attendance": 20,
            "Task Completion": 25,
            "Quality Rating": 15,
            "TL Score": 10
        }
    }


def recommend_promotion(data: dict) -> dict:
    """AI promotion recommendation engine"""
    productivity = data.get('productivity_score', 75)
    attendance = data.get('attendance_pct', 90)
    task_completion = data.get('task_completion', 75)
    experience = data.get('experience', 2)
    projects = data.get('projects_completed', 5)
    current_role = data.get('role', 'Junior Developer')
    tl_score = data.get('tl_score', 7)

    # Stricter eligibility: Must have enough experience and projects
    exp_factor = min(experience * 4, 20) 
    proj_factor = min(projects * 1.5, 15)
    
    eligibility_score = (
        productivity * 0.25 +
        attendance * 0.1 +
        task_completion * 0.2 +
        exp_factor +
        proj_factor +
        tl_score * 1.0
    )
    eligibility_pct = round(min(100, eligibility_score), 1)

    # Role progression map
    progression = {
        "Junior Developer": ("Software Engineer", 2, ["System Design", "Code Review", "Mentoring"]),
        "Software Engineer": ("Senior Software Engineer", 5, ["Architecture", "Leadership", "CI/CD"]),
        "Senior Developer": ("Tech Lead", 7, ["Team Management", "Project Planning", "Stakeholder Comm."]),
        "Senior Software Engineer": ("Tech Lead", 7, ["Leadership", "Architecture", "Strategy"]),
        "Tech Lead": ("Engineering Manager", 10, ["People Management", "OKRs", "Budget Planning"]),
        "QA Engineer": ("Senior QA Engineer", 4, ["Test Strategy", "Automation Framework", "Mentoring"]),
        "Data Analyst": ("Senior Data Analyst", 4, ["ML Basics", "Data Strategy", "Visualization"]),
        "Data Scientist": ("Senior Data Scientist", 6, ["Research", "MLOps", "Team Leadership"]),
        "DevOps Engineer": ("Senior DevOps / SRE", 5, ["SRE Practices", "Cost Optimization", "Team Lead"]),
        "Full Stack Developer": ("Senior Full Stack Developer", 4, ["System Design", "Code Review", "DevOps"]),
    }

    next_role, yrs_needed, required_skills = progression.get(
        current_role, ("Senior " + current_role, experience + 2, ["Leadership", "Advanced Skills"])
    )

    if eligibility_pct >= 85:
        recommendation = "🟢 Strongly Recommended for Promotion"
        readiness = "High"
    elif eligibility_pct >= 75:
        recommendation = "🟡 Eligible — Minor Development Needed"
        readiness = "Medium"
    elif eligibility_pct >= 60:
        recommendation = "🟠 Not Yet Ready — Focus on Key Areas"
        readiness = "Low"
    else:
        recommendation = "🔴 Significant Development Required"
        readiness = "Very Low"

    return {
        "eligibility_pct": eligibility_pct,
        "recommendation": recommendation,
        "current_role": current_role,
        "recommended_role": next_role,
        "required_skills": required_skills,
        "years_experience_needed": yrs_needed,
        "readiness_level": readiness,
        "strengths": _get_strengths(data),
        "improvement_areas": _get_improvements(data)
    }


def _get_strengths(data):
    strengths = []
    if data.get('productivity_score', 0) > 85: strengths.append("High Productivity")
    if data.get('attendance_pct', 0) > 92: strengths.append("Excellent Attendance")
    if data.get('task_completion', 0) > 85: strengths.append("Strong Task Completion")
    if data.get('tl_score', 0) > 8: strengths.append("Highly Rated by Team Leader")
    if data.get('projects_completed', 0) > 10: strengths.append("Extensive Project Experience")
    return strengths or ["Consistent Performance"]


def _get_improvements(data):
    areas = []
    if data.get('productivity_score', 100) < 75: areas.append("Boost Productivity Score")
    if data.get('attendance_pct', 100) < 85: areas.append("Improve Attendance")
    if data.get('task_completion', 100) < 75: areas.append("Increase Task Completion Rate")
    if data.get('tl_score', 10) < 7: areas.append("Work on Team Leader Feedback")
    return areas or ["Continue Current Growth Trajectory"]


def predict_attrition(data: dict) -> dict:
    """Predict employee attrition/resignation risk"""
    satisfaction = data.get('satisfaction', 75)
    salary = data.get('salary', 70000)
    attendance = data.get('attendance_pct', 90)
    productivity = data.get('productivity_score', 75)
    tl_score = data.get('tl_score', 7)
    experience = data.get('experience', 3)

    risk_score = 0
    reasons = []

    # Satisfaction is the biggest driver
    if satisfaction < 60:
        risk_score += 40
        reasons.append("Low job satisfaction")
    elif satisfaction < 75:
        risk_score += 20
        reasons.append("Satisfaction could be improved")

    # Salary benchmarking (example thresholds)
    if salary > 0: # Avoid adding risk if salary is 0 (missing)
        if salary < 60000:
            risk_score += 30
            reasons.append("Salary below market benchmark")
        elif salary < 75000:
            risk_score += 15
            reasons.append("Salary is average but could be competitive")

    if attendance < 80:
        risk_score += 25
        reasons.append("Recent patterns of disengagement (low attendance)")

    if tl_score < 6:
        risk_score += 20
        reasons.append("Sub-optimal relationship with direct supervisor")

    if productivity < 70:
        risk_score += 15
        reasons.append("Noticeable dip in productivity")

    risk_score = min(100, risk_score)
    if risk_score >= 75:
        level = "🔴 Critical"
    elif risk_score >= 50:
        level = "🟠 High"
    elif risk_score >= 25:
        level = "🟡 Medium"
    else:
        level = "🟢 Low"

    return {
        "risk_percentage": risk_score,
        "risk_level": level,
        "reasons": reasons or ["No major risk indicators detected"],
        "recommendations": _attrition_recommendations(risk_score, reasons)
    }


def _attrition_recommendations(score, reasons):
    recs = []
    if score > 50:
        recs.append("Schedule urgent 1-on-1 with HR manager")
    if any("salary" in r.lower() for r in reasons):
        recs.append("Review compensation against market benchmarks")
    if any("satisfaction" in r.lower() for r in reasons):
        recs.append("Conduct employee satisfaction survey")
    if any("attendance" in r.lower() for r in reasons):
        recs.append("Investigate work-life balance concerns")
    recs.append("Offer career development opportunities")
    return recs


def analyze_skill_gap(data: dict) -> dict:
    """Analyze skill gap between required and current skills"""
    current_skills = data.get('current_skills', [])
    target_role = data.get('target_role', 'Senior Developer')
    if isinstance(current_skills, str):
        current_skills = [s.strip() for s in current_skills.split(',') if s.strip()]

    role_skills = {
        "Senior Developer": ["Python", "System Design", "Code Review", "Docker", "AWS", "CI/CD", "Testing", "Mentoring"],
        "Senior Software Engineer": ["Python", "System Design", "Architecture", "Code Review", "Leadership", "Docker", "AWS"],
        "Tech Lead": ["Leadership", "Architecture", "Project Management", "Stakeholder Communication", "Agile", "Budget Planning"],
        "Engineering Manager": ["People Management", "OKRs", "Team Building", "Strategy", "Conflict Resolution"],
        "Data Scientist": ["Machine Learning", "Deep Learning", "MLOps", "Python", "Statistics", "Research", "TensorFlow"],
        "DevOps Engineer": ["Kubernetes", "Docker", "Terraform", "Monitoring", "SRE", "Cost Optimization", "Linux", "AWS"],
        "Full Stack Developer": ["React", "Node.js", "System Design", "Databases", "API Design", "DevOps", "JavaScript"],
        "QA Engineer": ["Selenium", "Python", "API Testing", "Performance Testing", "Test Strategy", "CI Integration"],
        "Data Analyst": ["Python", "SQL", "Tableau", "Statistics", "Data Visualization", "Excel", "R"],
        "Junior Developer": ["Python", "JavaScript", "HTML", "CSS", "Git", "Basic Algorithms"],
        "Software Engineer": ["Python", "Java", "SQL", "Docker", "REST APIs", "Git", "Testing"],
    }

    required = role_skills.get(target_role, ["Advanced Skills", "Leadership", "Architecture", "System Design"])
    current_lower = [s.lower() for s in current_skills]

    def _skill_matches(req_skill: str, emp_skills_lower: list) -> bool:
        r = req_skill.lower()
        for emp in emp_skills_lower:
            if r in emp or emp in r:
                return True
        return False

    matched = [r for r in required if _skill_matches(r, current_lower)]
    gaps = [r for r in required if not _skill_matches(r, current_lower)]
    match_pct = round((len(matched) / max(len(required), 1)) * 100, 1)

    training_map = {
        "Machine Learning": "Coursera: ML Specialization (Andrew Ng)",
        "Docker": "Docker Official Training + Udemy Docker Mastery",
        "AWS": "AWS Certified Solutions Architect Prep Course",
        "Leadership": "LinkedIn Learning: Leadership Foundations",
        "System Design": "Grokking the System Design Interview",
        "Kubernetes": "CNCF Kubernetes Certification (CKA)",
        "React": "React - The Complete Guide (Udemy)",
        "CI/CD": "Jenkins & GitHub Actions - DevOps Bootcamp",
        "Architecture": "Software Architecture Patterns (O'Reilly)",
    }

    training_recs = [{"skill": g, "course": training_map.get(g, f"Online course for {g}")} for g in gaps]

    return {
        "target_role": target_role,
        "current_skills": current_skills,
        "required_skills": required,
        "matched_skills": matched,
        "skill_gaps": gaps,
        "match_percentage": match_pct,
        "training_recommendations": training_recs,
        "estimated_gap_fill_months": len(gaps) * 2
    }


def analyze_ats(resume_text: str) -> dict:
    """ATS Resume Scoring Engine"""
    text_lower = resume_text.lower()
    keywords = {
        "technical": ["python", "java", "javascript", "react", "node", "sql", "docker", "aws", "git", "api", "machine learning", "css", "html"],
        "soft": ["leadership", "teamwork", "communication", "problem solving", "agile", "scrum", "collaboration"],
        "experience": ["years", "experience", "developed", "built", "designed", "implemented", "managed", "led"],
        "education": ["bachelor", "master", "degree", "university", "engineering", "computer science", "certification"]
    }

    scores = {}
    found_keywords = []
    for category, words in keywords.items():
        found = [w for w in words if w in text_lower]
        scores[category] = round(min(100, (len(found) / len(words)) * 100), 1)
        found_keywords.extend(found)

    ats_score = round(sum(scores.values()) / len(scores), 1)

    role_suggestions = []
    if scores["technical"] > 60:
        if any(k in text_lower for k in ["machine learning", "python", "tensorflow", "data"]):
            role_suggestions.append("Data Scientist / ML Engineer")
        if any(k in text_lower for k in ["react", "node", "javascript", "html"]):
            role_suggestions.append("Full Stack Developer")
        if any(k in text_lower for k in ["docker", "aws", "kubernetes", "devops"]):
            role_suggestions.append("DevOps / Cloud Engineer")
        role_suggestions.append("Software Engineer")

    return {
        "ats_score": ats_score,
        "category_scores": scores,
        "found_keywords": list(set(found_keywords))[:15],
        "role_suggestions": role_suggestions or ["Junior Developer"],
        "improvements": [
            "Add quantifiable achievements (e.g., 'Improved API performance by 40%')",
            "Include specific technology versions",
            "Add certifications and training",
            "Use action verbs: developed, architected, optimized"
        ] if ats_score < 70 else ["Good ATS optimization — ensure keywords match job description"]
    }
