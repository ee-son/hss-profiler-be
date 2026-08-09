import asyncio

from flask import Blueprint, jsonify, request

from services.profiler import profile_user
from services.cache import get_all_profiles, save_profile, delete_profile
from services.lang_detector import WrongLanguageError
from services.auth import check_admin_key

admin_bp = Blueprint("admin", __name__)

def require_admin():
    api_key = request.headers.get("X-Admin-Key")

    if not check_admin_key(api_key):
        return jsonify({
            "error": "Unauthorized."
        }), 401

    return None

# Route get all profiles
@admin_bp.route("/api/admin/profiles", methods=["GET"])
def admin_profiles():
    auth_error = require_admin()

    if auth_error:
        return auth_error

    try:
        profiles = get_all_profiles()

        return jsonify({
            "profiles": profiles
        })

    except Exception as e:
        print(e)

        return jsonify({
            "error": "Internal server error."
        }), 500

# Route update profile
@admin_bp.route("/api/admin/profiles/<username>/<language>", methods=["POST"])
def update_profile(username, language):
    auth_error = require_admin()

    if auth_error:
        return auth_error

    if language not in ["id", "en", "es"]:
        return jsonify({
            "error": "Language must be one of: id, en, es."
        }), 400

    try:
        result = asyncio.run(
            profile_user(
                username=username,
                language=language,
                explain=True,
                force_refresh=True
            )
        )

        return jsonify({
            "message": "Profile updated successfully.",
            "username": username,
            "language": language,
            "last_updated": result.get("last_updated"),
            "result": result
        })

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

# Route delete profile
@admin_bp.route("/api/admin/profiles/<username>/<language>", methods=["DELETE"])
def delete_admin_profile(username, language):
    auth_error = require_admin()

    if auth_error:
        return auth_error

    if language not in ["id", "en", "es"]:
        return jsonify({
            "error": "Language must be one of: id, en, es."
        }), 400

    try:
        delete_profile(
            username,
            language
        )

        return jsonify({
            "message": "Profile deleted successfully.",
            "username": username,
            "language": language
        })

    except Exception as e:
        print(e)

        return jsonify({
            "error": "Internal server error."
        }), 500
