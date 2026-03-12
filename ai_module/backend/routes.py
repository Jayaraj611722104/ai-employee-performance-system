# PulseHR AI Performance Module APIs
# =================================

@app.route('/api/ai/employee-data')
@login_required(roles=['hr', 'admin'])
def get_ai_employee_data():
    db = get_db_data()
    uid = request.args.get('user_id')
    if not uid:
        return jsonify({'success': False, 'message': 'user_id is required'}), 400
    
    emp = next((e for e in db['employees'] if e['user_id'] == uid), None)
    perf = next((p for p in db['performance'] if p['user_id'] == uid), None)
    
    if not emp:
        return jsonify({'success': False, 'message': 'Employee not found'}), 404
        
    return jsonify({
        'success': True,
        'employee': emp,
        'performance': perf or {}
    })

@app.route('/api/ai/productivity-score', methods=['POST'])
@login_required(roles=['hr', 'admin'])
def calculate_productivity_score():
    data = request.get_json()
    metrics = ai_service.calculate_metrics(data)
    return jsonify({
        'success': True,
        'metrics': metrics
    })

@app.route('/api/ai/performance-prediction', methods=['POST'])
@login_required(roles=['hr', 'admin'])
def predict_performance():
    data = request.get_json()
    metrics = data.get('metrics')
    rating = data.get('manager_rating', 3)
    exp = data.get('experience_years', 1)
    
    prediction, probability = ai_service.predict_performance(metrics, rating, exp)
    
    return jsonify({
        'success': True,
        'predicted_performance': prediction,
        'probability': probability
    })

@app.route('/api/ai/promotion-recommendation', methods=['POST'])
@login_required(roles=['hr', 'admin'])
def get_promotion_recommendation():
    data = request.get_json()
    p_score = data.get('productivity_score', 0)
    a_score = data.get('attendance_score', 0)
    exp = data.get('experience_years', 0)
    rating = data.get('manager_rating', 0)
    
    status = ai_service.get_promotion_recommendation(p_score, a_score, exp, rating)
    
    return jsonify({
        'success': True,
        'promotion_status': status
    })

@app.route('/api/ai/full-analysis/<uid>')
@login_required(roles=['hr', 'admin'])
def get_full_ai_analysis(uid):
    db = get_db_data()
    emp = next((e for e in db['employees'] if e['user_id'] == uid), None)
    perf = next((p for p in db['performance'] if p['user_id'] == uid), None)
    
    if not emp:
        return jsonify({'success': False, 'message': 'Employee not found'}), 404
    
    # Mock some raw data for analysis if not present
    # In a real app, these would come from the database
    raw_data = {
        'present_days': perf.get('attendance_pct', 90) * 0.22 if perf else 20,
        'total_working_days': 22,
        'completed_tasks': perf.get('task_completion', 80) * 0.1 if perf else 8,
        'assigned_tasks': 10,
        'bug_rate': 5,
        'rework_rate': 2,
        'peer_review_score': perf.get('satisfaction', 80) if perf else 85
    }
    
    metrics = ai_service.calculate_metrics(raw_data)
    prediction, prob = ai_service.predict_performance(metrics, perf.get('tl_score', 3) if perf else 3, emp.get('experience', 1))
    promo_status = ai_service.get_promotion_recommendation(metrics['productivity_score'], metrics['attendance_score'], emp.get('experience', 1), perf.get('tl_score', 3) if perf else 3)
    
    return jsonify({
        'success': True,
        'name': emp['name'],
        'metrics': metrics,
        'prediction': prediction,
        'probability': prob,
        'recommendation': promo_status
    })
