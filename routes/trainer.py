import os
import uuid
import subprocess
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, session, redirect, url_for
from functools import wraps
from database import questions_collection, users_collection
from bson.objectid import ObjectId

trainer_bp = Blueprint('trainer', __name__)

# --- Authentication Middleware ---
def trainer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'trainer':
            return redirect(url_for('auth.login', msg='unauthorized'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@trainer_bp.route('/trainer')
@trainer_required
def trainer_dashboard():
    from database import logs_collection # Ensure this is imported
    
    trainer_data = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    my_questions = list(questions_collection.find({"author_id": session['user_id']}).sort("created_at", -1))
    
    # NEW: Fetch global settings so we know what libraries are allowed
# NEW: Fetch global settings so we know what libraries are allowed
    settings_collection = logs_collection.database['global_settings']
    global_settings = settings_collection.find_one({"_id": "global_policy"})
    if not global_settings:
        global_settings = {
            "allow_tailwind": True, 
            "allow_bootstrap": True, 
            "allow_react": False,
            "strict_mode": True # Add this line
        }
    
    return render_template(
        'trainer.html', 
        name=trainer_data.get('name', 'Trainer'),
        trainer_id=trainer_data.get('trainer_id', 'N/A'),
        classes=trainer_data.get('trainer_classes', []),
        questions=my_questions,
        settings=global_settings # Pass it to the template!
    )

@trainer_bp.route('/api/questions', methods=['POST'])
@trainer_required
def create_question():
    data = request.json
    question_id = f"q_{uuid.uuid4().hex[:8]}"
    
    question_doc = {
        "question_id": question_id,
        "title": data.get("title", "Untitled Task"),
        "description": data.get("description", ""),
        "allowed_libraries": data.get("allowed_libraries", []),
        "spec": data.get("spec", {}),
        "target_class": data.get("target_class", "All"),
        "author_id": session['user_id'], # Link question to the trainer
        "created_at": datetime.utcnow()
    }
    
    questions_collection.insert_one(question_doc)
    return jsonify({"message": "Question created successfully", "question_id": question_id}), 201

@trainer_bp.route('/api/questions/<question_id>', methods=['DELETE'])
@trainer_required
def delete_question(question_id):
    # Security: Ensure they only delete questions they authored
    result = questions_collection.delete_one({
        "question_id": question_id, 
        "author_id": session['user_id']
    })
    
    if result.deleted_count == 1:
        # Optional: You could also write `os.remove()` here to delete the 
        # html, css, js, and png files from the server to save space!
        return jsonify({"message": "Question deleted successfully"}), 200
        
    return jsonify({"error": "Question not found or unauthorized"}), 404

@trainer_bp.route('/api/questions/<question_id>/baseline', methods=['POST'])
@trainer_required
def generate_baseline(question_id):
    data = request.json
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    html_path = os.path.join(upload_folder, f"{question_id}_ref.html")
    css_path = os.path.join(upload_folder, f"{question_id}_ref.css")
    js_path = os.path.join(upload_folder, f"{question_id}_ref.js")
    
    with open(html_path, 'w', encoding='utf-8') as f: f.write(data.get('html', ''))
    with open(css_path, 'w', encoding='utf-8') as f: f.write(data.get('css', ''))
    with open(js_path, 'w', encoding='utf-8') as f: f.write(data.get('js', ''))
    
    try:
        # Trigger Puppeteer to capture the Golden Baseline
        cmd = ['node', 'eval_engine/evaluate.js', 'baseline', question_id, html_path, css_path, js_path]
        
        # CRITICAL: encoding='utf-8' prevents Windows charmap crashes!
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=os.name == 'nt', encoding='utf-8')
        
        expected_image = f"/workspace/baselines/{question_id}_baseline.png"
        
        # Save the baseline image path directly into the question document
        questions_collection.update_one(
            {"question_id": question_id},
            {"$set": {"baseline_image": expected_image, "has_baseline": True}}
        )
        
        return jsonify({"message": "Baseline generated", "image_path": expected_image, "logs": result.stdout}), 200
        
    except subprocess.CalledProcessError as e:
        print(f"Node Engine Error: {e.stderr}")
        return jsonify({"error": "Failed to generate baseline", "details": e.stderr}), 500