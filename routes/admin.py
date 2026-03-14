import os
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from database import logs_collection, questions_collection, users_collection
from bson.objectid import ObjectId

admin_bp = Blueprint('admin', __name__)

# Dynamically create/access a settings collection
settings_collection = logs_collection.database['global_settings']

# Optional: Add @admin_required middleware if you have Admin login setup
@admin_bp.route('/admin')
def admin_dashboard():
    return render_template('admin.html')

@admin_bp.route('/api/admin/kpis', methods=['GET'])
def get_kpis():
    total_submissions = logs_collection.count_documents({"type": {"$ne": "malpractice_alert"}})
    malpractice_flags = logs_collection.count_documents({"type": "malpractice_alert"})
    total_tasks = questions_collection.count_documents({})
    
    # Calculate Average Score across the platform
    pipeline = [
        {"$match": {"type": {"$ne": "malpractice_alert"}}},
        {"$group": {"_id": None, "avg_score": {"$avg": "$score"}}}
    ]
    score_res = list(logs_collection.aggregate(pipeline))
    avg_score = round(score_res[0]['avg_score'], 1) if score_res and score_res[0]['avg_score'] is not None else 0

    return jsonify({
        "total_submissions": total_submissions,
        "avg_score": avg_score,
        "total_tasks": total_tasks,
        "malpractice_flags": malpractice_flags
    }), 200

@admin_bp.route('/api/admin/evaluation_runs', methods=['GET'])
def get_evaluation_runs():
    from bson.objectid import ObjectId # Ensure ObjectId is imported!
    
    logs = list(logs_collection.find({"type": {"$ne": "malpractice_alert"}}, {'_id': 0}).sort('timestamp', -1).limit(200))
    for log in logs:
        if 'timestamp' in log and isinstance(log['timestamp'], datetime):
            log['timestamp'] = log['timestamp'].isoformat()
        
        # --- BULLETPROOF STUDENT LOOKUP ---
        log['student_name'] = 'Unknown'
        if 'student_id' in log and log['student_id']:
            s_id = log['student_id']
            user = None
            
            try:
                # Attempt 1: Search as a MongoDB ObjectId
                user = users_collection.find_one({"_id": ObjectId(s_id)})
            except:
                pass
                
            if not user:
                # Attempt 2: Search as a plain string
                user = users_collection.find_one({"_id": s_id})
                
            if user:
                # Combine Name and Register Number if available!
                name = user.get('name', 'Unknown')
                reg = user.get('register_number', '')
                log['student_name'] = f"{name} ({reg})" if reg else name

    return jsonify(logs), 200

@admin_bp.route('/api/admin/malpractice_logs', methods=['GET'])
def get_malpractice_logs():
    from bson.objectid import ObjectId # Ensure ObjectId is imported!
    
    logs = list(logs_collection.find({"type": "malpractice_alert"}, {'_id': 0}).sort('timestamp', -1).limit(100))
    for log in logs:
        if 'timestamp' in log and isinstance(log['timestamp'], datetime):
            log['timestamp'] = log['timestamp'].isoformat()
            
        # --- BULLETPROOF STUDENT LOOKUP ---
        log['student_name'] = 'Unknown'
        if 'student_id' in log and log['student_id']:
            s_id = log['student_id']
            user = None
            
            try:
                user = users_collection.find_one({"_id": ObjectId(s_id)})
            except:
                pass
                
            if not user:
                user = users_collection.find_one({"_id": s_id})
                
            if user:
                name = user.get('name', 'Unknown')
                reg = user.get('register_number', '')
                log['student_name'] = f"{name} ({reg})" if reg else name

    return jsonify(logs), 200

@admin_bp.route('/api/admin/settings', methods=['GET', 'POST'])
def manage_settings():
    if request.method == 'POST':
        data = request.json
        settings_collection.update_one(
            {"_id": "global_policy"},
            {"$set": data},
            upsert=True
        )
        return jsonify({"status": "success"}), 200
    else:
        settings = settings_collection.find_one({"_id": "global_policy"}, {'_id': 0})
        # Default policy if never saved
        if not settings:
            settings = {
                "allow_tailwind": True, 
                "allow_bootstrap": True, 
                "allow_react": False,
                "strict_mode": True # NEW: Default to Strict Mode ON
            }
        return jsonify(settings), 200
    
@admin_bp.route('/api/admin/trainers_info', methods=['GET'])
def get_trainers_info():
    # Fetch all trainers
    trainers = list(users_collection.find({"role": "trainer"}, {'password': 0}))
    
    for t in trainers:
        t['_id'] = str(t['_id'])
        classes = t.get('trainer_classes', [])
        
        # --- BULLETPROOF STUDENT LOOKUP ---
        # Checks multiple possible field names where the student's class might be stored
        students = list(users_collection.find({
            "role": "student", 
            "$or": [
                {"target_class": {"$in": classes}},
                {"class": {"$in": classes}},
                {"student_class": {"$in": classes}},
                {"department": {"$in": classes}}
            ]
        }, {'password': 0}))
        
        for s in students:
            s['_id'] = str(s['_id'])
            
        t['students'] = students
        t['student_count'] = len(students)
        
    return jsonify(trainers), 200