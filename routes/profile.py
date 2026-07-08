from flask import Blueprint, request, jsonify

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/api/profile", methods=["POST"])
def profile():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    username = data.get("username")

    if not username:
        return jsonify({
            "error": "Username is required."
        }), 400

    return jsonify({
        "username": username,
        "status": "received"
    })