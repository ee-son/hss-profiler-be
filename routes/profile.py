import asyncio
from flask import Blueprint, jsonify, request
from services.profiler import profile_user
from services.lang_detector import WrongLanguageError

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/api/profile", methods=["POST"])
def profile():
    """
    Profile a user and detect potential hate speech behavior.

    ---
    tags:
      - Profile

    consumes:
      - application/json

    produces:
      - application/json

    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - language
          properties:
            username:
              type: string
              example: "example_user"
              description: Username to be profiled.
            language:
              type: string
              enum:
                - id
                - en
                - es
              example: "id"
              description: Language used for profiling.
            explain:
              type: boolean
              example: false
              default: false
              description: Whether to include an explanation in the result.

    responses:
      200:
        description: Profiling successful.
        schema:
          type: object
          example:
            username: "example_user"
            score: 0.75
            label: "hate_speech_spreader"

      400:
        description: Invalid request.
        schema:
          type: object
          properties:
            error:
              type: string
          examples:
            missing_body:
              value:
                error: "Need body JSON."
            invalid_username:
              value:
                error: "Username must be filled."
            invalid_language:
              value:
                error: "Language must be one of: id, en, es."

      429:
        description: Rate limit or service limit exceeded.
        schema:
          type: object
          properties:
            error:
              type: string

      500:
        description: Internal server error.
        schema:
          type: object
          properties:
            error:
              type: string
    """
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
    