import hmac
import hashlib
import time
import base64
import json
from functools import wraps
from flask import request, jsonify, current_app

def generate_auth_token(username, role='Academic Office', expires_in=86400):
    """
    Generates a secure signed JSON web token using HMAC-SHA256.
    """
    secret = current_app.config['SECRET_KEY'].encode('utf-8')
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in
    }
    
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode('utf-8')).decode('utf-8').rstrip('=')
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8').rstrip('=')
    
    msg = f"{h_b64}.{p_b64}".encode('utf-8')
    sig = hmac.new(secret, msg, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode('utf-8').rstrip('=')
    
    return f"{h_b64}.{p_b64}.{sig_b64}"

def verify_auth_token(token):
    """
    Verifies token signature and expiration.
    Returns: (is_valid: bool, payload: dict or None, error: str)
    """
    if not token:
        return False, None, "Missing authentication token."
        
    parts = token.split('.')
    if len(parts) != 3:
        return False, None, "Malformed token format."
        
    h_b64, p_b64, sig_b64 = parts
    secret = current_app.config['SECRET_KEY'].encode('utf-8')
    msg = f"{h_b64}.{p_b64}".encode('utf-8')
    expected_sig = hmac.new(secret, msg, hashlib.sha256).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8').rstrip('=')
    
    if not hmac.compare_digest(sig_b64, expected_sig_b64):
        return False, None, "Invalid token signature."
        
    try:
        # Pad base64 if needed
        p_padded = p_b64 + '=' * (-len(p_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(p_padded.encode('utf-8')).decode('utf-8'))
    except Exception as e:
        return False, None, f"Could not decode token payload: {e}"
        
    if payload.get('exp', 0) < time.time():
        return False, None, "Token has expired. Please log in again."
        
    return True, payload, None

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()
        elif 'token' in request.args:
            token = request.args.get('token')

        valid, payload, error = verify_auth_token(token)
        if not valid:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access.',
                'details': error
            }), 401

        request.user = payload
        return f(*args, **kwargs)
    return decorated
