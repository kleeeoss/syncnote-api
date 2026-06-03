from flask import Flask, jsonify
from database import get_db_connection, release_db_connection
from routes.auth import auth_bp
from routes.notes import notes_bp

app = Flask(__name__)

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(notes_bp, url_prefix='/api/notes')

@app.route('/')
def home():
    return jsonify({"message": "SyncNote API is running 🚀"})

@app.route('/test-db')
def test_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        cur.close()
        release_db_connection(conn)
        return jsonify({"database": db_version[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)