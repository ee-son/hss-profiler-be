import asyncio

from flask import Blueprint, jsonify, request

from services.profiler import profile_user
from services.cache import get_profile, get_all_profiles, delete_profile
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
    """
    Get all profiles.

    ---
    tags:
      - Admin - Profiles

    security:
      - AdminKey: []

    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        minimum: 1
        description: Page number.

      - name: per_page
        in: query
        type: integer
        required: false
        default: 20
        minimum: 1
        maximum: 100
        description: Number of profiles per page.

      - name: search
        in: query
        type: string
        required: false
        default: ""
        description: Search profiles by username.

      - name: sort_by
        in: query
        type: string
        required: false
        default: last_updated
        enum:
          - username
          - language
          - last_updated
        description: Field used for sorting.

      - name: sort_order
        in: query
        type: string
        required: false
        default: desc
        enum:
          - asc
          - desc
        description: Sort direction.

    responses:
      200:
        description: Profiles retrieved successfully.
        schema:
          type: object
          example:
            page: 1
            per_page: 20
            total: 42
            total_pages: 3
            profiles:
              - username: "example_user"
                language: "id"
                last_updated: "2026-08-19T12:00:00Z"

      400:
        description: Invalid query parameters.
        schema:
          type: object
          properties:
            error:
              type: string
          examples:
            invalid_page:
              value:
                error: "Page must be greater than 0."
            invalid_per_page:
              value:
                error: "per_page must be between 1 and 100."
            invalid_sort_field:
              value:
                error: "Invalid sort field."
            invalid_sort_order:
              value:
                error: "Invalid sort order."

      401:
        description: Unauthorized. Invalid or missing admin API key.
        schema:
          type: object
          example:
            error: "Unauthorized."

      500:
        description: Internal server error.
        schema:
          type: object
          example:
            error: "Internal server error."
    """
    auth_error = require_admin()

    if auth_error:
        return auth_error

    try:
        page = request.args.get(
            "page",
            default=1,
            type=int
        )

        per_page = request.args.get(
            "per_page",
            default=20,
            type=int
        )

        search = request.args.get(
            "search",
            default=""
        ).strip()

        sort_by = request.args.get(
            "sort_by",
            default="last_updated"
        )

        sort_order = request.args.get(
            "sort_order",
            default="desc"
        )

        if page < 1:
            return jsonify({
                "error": "Page must be greater than 0."
            }), 400

        if per_page < 1 or per_page > 100:
            return jsonify({
                "error": "per_page must be between 1 and 100."
            }), 400

        if sort_by not in {
            "username",
            "language",
            "last_updated"
        }:
            return jsonify({
                "error": "Invalid sort field."
            }), 400

        if sort_order not in {
            "asc",
            "desc"
        }:
            return jsonify({
                "error": "Invalid sort order."
            }), 400

        result = get_all_profiles(
            page=page,
            per_page=per_page,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return jsonify(result)

    except Exception as e:
        print(e)

        return jsonify({
            "error": "Internal server error."
        }), 500

# Get one profile
@admin_bp.route("/api/admin/profiles/<username>/<language>", methods=["GET"])
def view_profile(username, language):
    """
    Get a single user profile.

    ---
    tags:
      - Admin - Profiles

    security:
      - AdminKey: []

    parameters:
      - name: username
        in: path
        type: string
        required: true
        description: Username of the profile.
        example: example_user

      - name: language
        in: path
        type: string
        required: true
        enum:
          - id
          - en
          - es
        description: Profile language.
        example: id

    responses:
      200:
        description: Profile retrieved successfully.
        schema:
          type: object
          example:
            username: "example_user"
            language: "id"
            last_updated: "2026-08-19T12:00:00Z"
            score: 0.75
            label: "hate_speech_spreader"

      400:
        description: Invalid language.
        schema:
          type: object
          example:
            error: "Language must be one of: id, en, es."

      401:
        description: Unauthorized. Invalid or missing admin API key.
        schema:
          type: object
          example:
            error: "Unauthorized."

      404:
        description: Profile not found.
        schema:
          type: object
          example:
            error: "Profile not found."
    """
    auth_error = require_admin()

    if auth_error:
        return auth_error

    if language not in ["id", "en", "es"]:
        return jsonify({
            "error": "Language must be one of: id, en, es."
        }), 400

    profile = get_profile(
        username=username,
        language=language
    )

    if profile is None:
        return jsonify({
            "error": "Profile not found."
        }), 404

    return jsonify(profile)

# Route update profile
@admin_bp.route("/api/admin/profiles/<username>/<language>", methods=["POST"])
def update_profile(username, language):
    """
    Force refresh and update a user profile.

    ---
    tags:
      - Admin - Profiles

    security:
      - AdminKey: []

    parameters:
      - name: username
        in: path
        type: string
        required: true
        description: Username of the profile to update.
        example: example_user

      - name: language
        in: path
        type: string
        required: true
        enum:
          - id
          - en
          - es
        description: Profile language.
        example: id

    responses:
      200:
        description: Profile updated successfully.
        schema:
          type: object
          example:
            message: "Profile updated successfully."
            username: "example_user"
            language: "id"
            last_updated: "2026-08-19T12:00:00Z"
            result:
              username: "example_user"
              language: "id"
              score: 0.75
              label: "hate_speech_spreader"

      400:
        description: Invalid language.
        schema:
          type: object
          example:
            error: "Language must be one of: id, en, es."

      401:
        description: Unauthorized. Invalid or missing admin API key.
        schema:
          type: object
          example:
            error: "Unauthorized."

      429:
        description: Rate limit or service limit exceeded.
        schema:
          type: object
          example:
            error: "Rate limit exceeded."

      500:
        description: Internal server error.
        schema:
          type: object
          example:
            error: "Internal server error."
    """
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
    """
    Delete a user profile.

    ---
    tags:
      - Admin - Profiles

    security:
      - AdminKey: []

    parameters:
      - name: username
        in: path
        type: string
        required: true
        description: Username of the profile to delete.
        example: example_user

      - name: language
        in: path
        type: string
        required: true
        enum:
          - id
          - en
          - es
        description: Profile language.
        example: id

    responses:
      200:
        description: Profile deleted successfully.
        schema:
          type: object
          example:
            message: "Profile deleted successfully."
            username: "example_user"
            language: "id"

      400:
        description: Invalid language.
        schema:
          type: object
          example:
            error: "Language must be one of: id, en, es."

      401:
        description: Unauthorized. Invalid or missing admin API key.
        schema:
          type: object
          example:
            error: "Unauthorized."

      500:
        description: Internal server error.
        schema:
          type: object
          example:
            error: "Internal server error."
    """
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
