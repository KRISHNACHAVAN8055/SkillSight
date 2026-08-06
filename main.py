from flask import Flask
from dashboard.routes import bp
from extensions import limiter
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set. Set it before running the app.")

limiter.init_app(app)
limiter._default_limits = ["200 per day", "50 per hour"]

app.register_blueprint(bp)

if __name__ == '__main__':
    from startup import check_and_seed
    check_and_seed()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
