import asyncio
from flask import Blueprint, jsonify, request
from services.profiler import profile_user

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/api/profile", methods=["POST"])
def profile():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Need body JSON."
        }), 400

    username = data.get("username")

    if not username:
        return jsonify({
            "error": "Username must be filled."
        }), 400

    result = asyncio.run(profile_user(username))

    return jsonify(result)