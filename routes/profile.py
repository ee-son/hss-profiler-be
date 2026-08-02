import asyncio
from flask import Blueprint, jsonify, request
from services.profiler import profile_user

from services.lang_detector import WrongLanguageError

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/api/profile", methods=["POST"])
def profile():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Need body JSON."
        }), 400

    username = data.get("username")
    language = data.get("language")
    explain = data.get("explain", False)

    if not username:
        return jsonify({
            "error": "Username must be filled."
        }), 400
    
    if language not in ["id", "en", "es"]:
        return jsonify({
            "error": "Language must be one of: id, en, es."
        }), 400

    try:
        result = asyncio.run(
            profile_user(
                username,
                language,
                explain
            )
        )

        return jsonify(result)

    except WrongLanguageError as e:
        return jsonify({
            "error": str(e)
        }), 400

    except RuntimeError as e:
        return jsonify({
            "error": str(e)
        }), 429
    
    except Exception as e:
        print(e)

        return jsonify({
            "error": "Internal server error."
        }), 500