import os
import json
import uuid
import subprocess
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, session, redirect, url_for
from functools import wraps
from database import questions_collection, logs_collection, users_collection
from bson.objectid import ObjectId

student_bp = Blueprint('student', __name__)

# --- Authentication Middleware ---
def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'student':
            return redirect(url_for('auth.login', msg='unauthorized'))
        return f(*args, **kwargs)
    return decorated_function


@student_bp.route('/dashboard')
@student_required
def student_dashboard():
    # Fetch student details
    student_data = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    
    # NEW: Fetch Global Policy for Strict Mode
    settings_collection = logs_collection.database['global_settings']
    global_settings = settings_collection.find_one({"_id": "global_policy"}) or {}
    strict_mode = global_settings.get("strict_mode", True)
    
    return render_template(
        'index.html',
        name=student_data.get('name', 'Student'),
        reg_num=student_data.get('register_number', 'N/A'),
        strict_mode=strict_mode # Pass it to the template!
    )
@student_bp.route('/api/questions/<question_id>', methods=['GET'])
@student_required
def get_question(question_id):
    question = questions_collection.find_one({"question_id": question_id})
    if not question:
        return jsonify({"error": "Task not found."}), 404
    
    # NEW: Fetch the Admin's Strict Mode setting dynamically!
    settings_collection = logs_collection.database['global_settings']
    global_settings = settings_collection.find_one({"_id": "global_policy"}) or {}
    strict_mode = global_settings.get("strict_mode", True)
    
    return jsonify({
        "title": question.get('title'),
        "description": question.get('description'),
        "allowed_libraries": question.get('allowed_libraries', []),
        "baseline_image": question.get('baseline_image'),
        "strict_mode": strict_mode # Pass it dynamically to the IDE
    }), 200

# --- ANTI-CHEAT LOGGING ROUTE ---
@student_bp.route('/api/malpractice', methods=['POST'])
@student_required
def log_malpractice():
    data = request.json
    student_id = session['user_id']
    question_id = data.get('question_id')
    violation_type = data.get('violation_type') # e.g., 'tab_switch', 'exited_fullscreen'
    strike_count = data.get('strike_count')
    
    # Log this into the database so the Trainer can see it later
    logs_collection.insert_one({
        "type": "malpractice_alert",
        "student_id": student_id,
        "question_id": question_id,
        "violation_type": violation_type,
        "strike_count": strike_count,
        "timestamp": datetime.utcnow()
    })
    
    return jsonify({"status": "logged"}), 200

@student_bp.route('/api/submissions', methods=['POST'])
@student_required
def handle_submission():
    submission_id = f"sub_{uuid.uuid4().hex[:8]}"
    student_id = session['user_id'] # Securely pull from session!
    
    if request.is_json:
        data = request.json
        question_id = data.get('question_id')
        html_content = data.get('html', '')
        css_content = data.get('css', '')
        js_content = data.get('js', '')
    else:
        question_id = request.form.get('question_id')
        html_file = request.files.get('html_file')
        css_file = request.files.get('css_file')
        js_file = request.files.get('js_file')
        html_content = html_file.read().decode('utf-8') if html_file else ''
        css_content = css_file.read().decode('utf-8') if css_file else ''
        js_content = js_file.read().decode('utf-8') if js_file else ''

    question = questions_collection.find_one({"question_id": question_id})
    if not question:
        return jsonify({"error": f"Task ID '{question_id}' not found."}), 404

    upload_folder = current_app.config['UPLOAD_FOLDER']
    html_path = os.path.join(upload_folder, f"{submission_id}.html")
    css_path = os.path.join(upload_folder, f"{submission_id}.css")
    js_path = os.path.join(upload_folder, f"{submission_id}.js")
    rubric_path = os.path.join(upload_folder, f"{submission_id}_rubric.json")
    
    with open(html_path, 'w', encoding='utf-8') as f: f.write(html_content)
    with open(css_path, 'w', encoding='utf-8') as f: f.write(css_content)
    with open(js_path, 'w', encoding='utf-8') as f: f.write(js_content)
    with open(rubric_path, 'w', encoding='utf-8') as f: json.dump(question.get('spec', {}), f)

    try:
        cmd = ['node', 'eval_engine/evaluate.js', 'eval', submission_id, question_id, html_path, css_path, js_path, rubric_path]
        
        # --- FIX: FORCING UTF-8 ENCODING SO AI EMOJIS/TEXT DON'T CRASH WINDOWS ---
        subprocess.run(cmd, check=True, capture_output=True, text=True, shell=os.name == 'nt', encoding='utf-8')
        
        result_path = os.path.join(upload_folder, f"{submission_id}_result.json")
        with open(result_path, 'r', encoding='utf-8') as f:
            eval_results = json.load(f)
            
        logs_collection.insert_one({
            "submission_id": submission_id,
            "student_id": student_id,
            "question_id": question_id,
            "timestamp": datetime.utcnow(),
            "score": eval_results.get('evaluationRun', {}).get('totalScore', 0),
            "submitted_code": {
                "html": html_content,
                "css": css_content,
                "js": js_content
            },
            "image_paths": {
                "expected": eval_results.get('artifacts', {}).get('expectedImagePath'),
                "actual": eval_results.get('artifacts', {}).get('actualImagePath')
            },
            "breakdown_json": eval_results
        })
        
        return jsonify({"message": "Evaluation Complete", "results": eval_results}), 200

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Engine failed.", "details": e.stderr}), 500