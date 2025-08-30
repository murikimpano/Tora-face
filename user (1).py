from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import User, db

user_bp = Blueprint('user', __name__)

# --- Helper function ---
def validate_user_data(data, require_password=True):
    if not data:
        return False, "Nta makuru yatanzwe"
    if 'username' not in data or not data['username']:
        return False, "Username irakenewe"
    if 'email' not in data or not data['email']:
        return False, "Email irakenewe"
    if require_password and ('password' not in data or not data['password']):
        return False, "Password irakenewe"
    return True, ""

# --- Routes ---

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    is_valid, message = validate_user_data(data)
    if not is_valid:
        return jsonify({"error": message}), 400

    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email yamaze gukoreshwa"}), 409

    # Hash password
    hashed_password = generate_password_hash(data['password'], method='sha256')

    user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if 'username' in data and data['username']:
        user.username = data['username']

    if 'email' in data and data['email']:
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != user.id:
            return jsonify({"error": "Email yamaze gukoreshwa"}), 409
        user.email = data['email']

    if 'password' in data and data['password']:
        user.password = generate_password_hash(data['password'], method='sha256')

    db.session.commit()
    return jsonify(user.to_dict()), 200

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User yasibwe neza"}), 200

# --- Optional login route ---
@user_bp.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email na password birakenewe"}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({"error": "Email cyangwa password si byo"}), 401

    # Hashing-based authentication (or return JWT token if implemented)
    return jsonify({"message": f"Murakaza neza, {user.username}!"}), 200
