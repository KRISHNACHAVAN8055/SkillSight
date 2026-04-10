from flask import Flask
from dashboard.routes import bp
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'skillsight_secret_2026')
app.register_blueprint(bp)

if __name__ == '__main__':
    from startup import check_and_seed
    check_and_seed()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)