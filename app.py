from flask import Flask
from flask_cors import CORS
from services.cache import init_db

from routes.profile import profile_bp

app = Flask(__name__)
CORS(app)

init_db()

app.register_blueprint(profile_bp)

@app.route("/")
def home():
    return {
        "message": "Hate Speech Profiling API",
        "status": "running"
    }

if __name__ == "__main__":
    app.run(debug=True)