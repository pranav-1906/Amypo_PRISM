from flask import Blueprint, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import os

# 🚀 IMPORT YOUR CENTRAL DATABASE CONNECTION
from database import users_collection

auth_bp = Blueprint('auth', __name__)

# Security: Passkey required to create an Admin account
ADMIN_CREATION_PASSKEY = os.getenv('ADMIN_PASSKEY', 'PRISM-ROOT-2026')

@auth_bp.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    role = data.get('role')
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')

    # 1. Basic Validation
    if not all([email, password, name, role]):
        return jsonify({'error': 'Missing basic required fields.'}), 400

    if users_collection.find_one({'email': email}):
        return jsonify({'error': 'Email already registered. Please log in.'}), 400

    # 2. Base Document
    user_doc = {
        'name': name,
        'email': email,
        'password': generate_password_hash(password),
        'role': role
    }

    # 3. Role-Specific Data Extraction
    if role == 'student':
        user_doc['register_number'] = data.get('register_number')
        user_doc['student_class'] = data.get('student_class')
        user_doc['staff_id'] = data.get('staff_id') 
        
        if not all([user_doc['register_number'], user_doc['student_class'], user_doc['staff_id']]):
            return jsonify({'error': 'Missing required student details.'}), 400

    elif role == 'trainer':
        user_doc['trainer_classes'] = data.get('trainer_classes', [])
        user_doc['trainer_id'] = data.get('trainer_id')
        
        if not user_doc['trainer_classes'] or not user_doc['trainer_id']:
            return jsonify({'error': 'Missing required trainer details.'}), 400

    elif role == 'admin':
        provided_passkey = data.get('admin_passkey')
        if provided_passkey != ADMIN_CREATION_PASSKEY:
            return jsonify({'error': 'Invalid System Admin Passkey.'}), 403

    # 4. Save to Database
    user_id = users_collection.insert_one(user_doc).inserted_id

    # 5. Log User In
    session['user_id'] = str(user_id)
    session['role'] = role
    session['name'] = name

    return jsonify({'success': True, 'role': role, 'message': 'Account created successfully!'})


@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    user = users_collection.find_one({'email': email})

    # Validate user exists and password is correct
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid email or password.'}), 401
    
    # Ensure they are logging into the correct portal
    if user.get('role') != role:
        return jsonify({'error': f"Account found, but not registered as a {role}."}), 403

    # Log User In
    session['user_id'] = str(user['_id'])
    session['role'] = user['role']
    session['name'] = user['name']

    return jsonify({'success': True, 'role': user['role']})


@auth_bp.route('/api/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/login')  # This forces the browser to actually load the login page