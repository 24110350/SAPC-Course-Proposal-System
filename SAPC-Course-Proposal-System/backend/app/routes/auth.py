from flask import Blueprint, request, jsonify, current_app
from ..models import SessionLocal
from ..models.user import AdminUser
from ..services.email_service import EmailService
from ..utils.auth_helper import generate_auth_token, admin_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticates Academic Office administrator.
    """
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password are required.'}), 400

    session = SessionLocal()
    try:
        user = session.query(AdminUser).filter(AdminUser.username == username).first()
        authenticated = False
        user_role = 'Academic Office'

        if user and user.check_password(password):
            authenticated = True
            user_role = user.role
        elif username == current_app.config['ADMIN_USERNAME'] and password == current_app.config['ADMIN_PASSWORD']:
            authenticated = True

        if not authenticated:
            return jsonify({'success': False, 'error': 'Invalid username or password.'}), 401

        token = generate_auth_token(username=username, role=user_role)

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'username': username,
                'role': user_role
            },
            'message': 'Authentication successful.'
        }), 200
    finally:
        session.close()

@auth_bp.route('/me', methods=['GET'])
@admin_required
def get_current_user():
    """
    Validates current token and returns user profile.
    """
    return jsonify({
        'success': True,
        'user': {
            'username': request.user.get('sub'),
            'role': request.user.get('role', 'Academic Office')
        }
    }), 200

@auth_bp.route('/outbox', methods=['GET'])
@admin_required
def get_email_outbox():
    """
    Admin audit endpoint to view simulated/sent email records.
    """
    logs = EmailService.get_outbox_logs()
    return jsonify({
        'success': True,
        'count': len(logs),
        'emails': logs
    }), 200
