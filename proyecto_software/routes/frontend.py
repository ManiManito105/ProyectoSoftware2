from flask import Blueprint, render_template

# Serve the SPA `index.html` for main routes (single page app)
frontend_bp = Blueprint('frontend', __name__, template_folder='..', static_folder='..')


@frontend_bp.route('/', defaults={'path': ''})
@frontend_bp.route('/<path:path>')
def index(path):
    # Render the main SPA page for any frontend route
    return render_template('index.html')
