import os
from flask import Flask, render_template, send_from_directory, session
from dotenv import load_dotenv  # <-- Add this

# Load environment variables FIRST
load_dotenv()

# Import Blueprints
from routes.student import student_bp
from routes.trainer import trainer_bp
from routes.admin import admin_bp
from routes.auth import auth_bp  

app = Flask(__name__)

# Now it properly reads FLASK_SECRET_KEY from your .env image
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super-secret-prism-key-change-in-production')
# ==========================================
# 🛠️ CONFIGURATION & DIRECTORIES
# ==========================================
app.config['UPLOAD_FOLDER'] = os.path.join('workspace', 'temp_submissions')
app.config['BASELINE_FOLDER'] = os.path.join('workspace', 'baselines')
app.config['EVAL_IMAGES_FOLDER'] = os.path.join('static', 'eval_images')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 

# Ensure directories exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['BASELINE_FOLDER'], app.config['EVAL_IMAGES_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

# ==========================================
# 🔌 REGISTER BLUEPRINTS
# ==========================================
app.register_blueprint(student_bp)
app.register_blueprint(trainer_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp) # <-- Register auth blueprint

# ==========================================
# 🌐 GLOBAL ROUTES
# ==========================================
@app.route('/')
def landing_page():
    return render_template('landing.html')

# WE NEED THIS! Serves the standalone auth page we built
@app.route('/login')
def login_page():
    return render_template('login.html')

# Custom route to serve secure baseline images from the workspace folder
@app.route('/workspace/baselines/<filename>')
def serve_baseline(filename):
    return send_from_directory(app.config['BASELINE_FOLDER'], filename)

if __name__ == '__main__':
    print("🚀 Starting PRISM Engine on http://localhost:5000")
    print("✓ Modular Architecture Loaded")
    app.run(debug=True, port=5000)