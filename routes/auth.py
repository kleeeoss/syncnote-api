from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, release_db_connection
import psycopg2
import jwt
import datetime
import os
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    # 1. Get data from the request body
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 2. Validation
    if not username or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    # 3. Hash the password
    # This turns "mypassword" into "scrypt:32768:8:1$..."
    password_hash = generate_password_hash(password)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 4. Insert into Database
        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id, username;",
            (username, email, password_hash)
        )
        new_user = cur.fetchone()

        # Commit the transaction (Save changes)
        conn.commit()

        return jsonify({
            "message": "User registered successfully! 🚀",
            "user": {"id": new_user[0], "username": new_user[1]}
        }), 201

    except psycopg2.IntegrityError:
        # This catches duplicate usernames/emails
        conn.rollback()  # Undo the failed attempt
        return jsonify({"error": "Username or Email already exists"}), 409

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        # 5. Clean up
        cur.close()
        release_db_connection(conn)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 1. Find the user in the database
        cur.execute("SELECT id, username, password_hash FROM users WHERE username = %s;", (username,))
        user = cur.fetchone()

        # 2. Check if user exists AND password matches the hash
        # user[2] is the password_hash from the database
        if user and check_password_hash(user[2], password):

            # 3. Generate the VIP Wristband (JWT)
            # It contains the user ID and an expiration date (valid for 24 hours)
            token = jwt.encode({
                'user_id': user[0],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, os.getenv('JWT_SECRET'), algorithm='HS256')

            return jsonify({
                "message": "Login successful!",
                "token": token  # Hand the wristband to the user
            }), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        release_db_connection(conn)