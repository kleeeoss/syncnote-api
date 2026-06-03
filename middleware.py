from functools import wraps
from flask import request, jsonify
import jwt
import os


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 1. Look for the token in the Headers (Standard format: "Bearer <token>")
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'error': 'Token is missing! The bouncer says no.'}), 401

        try:
            # 2. Decode the token using our Secret Key
            data = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired! Please log in again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401

        # 3. If valid, pass the user_id to the actual route
        return f(current_user_id, *args, **kwargs)

    return decorated