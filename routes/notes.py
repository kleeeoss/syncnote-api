from flask import Blueprint, request, jsonify
from database import get_db_connection, release_db_connection
from middleware import token_required

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/', methods=['POST'])
@token_required
def create_note(current_user_id):
    data = request.get_json()
    title = data.get('title')
    content = data.get('content', '') # Content is optional

    if not title:
        return jsonify({"error": "Title is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Insert note and link it to the current_user_id
        cur.execute(
            "INSERT INTO notes (title, content, user_id) VALUES (%s, %s, %s) RETURNING id, title, content, created_at;",
            (title, content, current_user_id)
        )
        new_note = cur.fetchone()
        conn.commit()

        return jsonify({
            "message": "Note created! 📝",
            "note": {
                "id": new_note[0],
                "title": new_note[1],
                "content": new_note[2],
                "created_at": new_note[3]
            }
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        release_db_connection(conn)


@notes_bp.route('/', methods=['GET'])
@token_required # <--- THE BOUNCER IS ACTIVE
def get_notes(current_user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Fetch ONLY the notes belonging to this specific user
        cur.execute("SELECT id, title, content, created_at FROM notes WHERE user_id = %s ORDER BY created_at DESC;", (current_user_id,))
        notes = cur.fetchall()

        # Format the data into a list of dictionaries
        notes_list = []
        for note in notes:
            notes_list.append({
                "id": note[0],
                "title": note[1],
                "content": note[2],
                "created_at": note[3]
            })

        return jsonify({"notes": notes_list}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        release_db_connection(conn)

@notes_bp.route('/<int:note_id>', methods=['PUT'])
@token_required
def update_note(current_user_id, note_id):
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    if not title:
        return jsonify({"error": "Title is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # UPDATE the note ONLY IF it belongs to the current user
        cur.execute(
            """
            UPDATE notes 
            SET title = %s, content = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s AND user_id = %s 
            RETURNING id, title, content, updated_at;
            """,
            (title, content, note_id, current_user_id)
        )
        updated_note = cur.fetchone()

        if not updated_note:
            return jsonify({"error": "Note not found or unauthorized"}), 404

        conn.commit()
        return jsonify({
            "message": "Note updated! ✏️",
            "note": {
                "id": updated_note[0],
                "title": updated_note[1],
                "content": updated_note[2],
                "updated_at": updated_note[3]
            }
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        release_db_connection(conn)


@notes_bp.route('/<int:note_id>', methods=['DELETE'])
@token_required
def delete_note(current_user_id, note_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # DELETE the note ONLY IF it belongs to the current user
        cur.execute(
            "DELETE FROM notes WHERE id = %s AND user_id = %s RETURNING id;",
            (note_id, current_user_id)
        )
        deleted_note = cur.fetchone()

        if not deleted_note:
            return jsonify({"error": "Note not found or unauthorized"}), 404

        conn.commit()
        return jsonify({"message": f"Note {note_id} deleted successfully! 🗑️"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        release_db_connection(conn)