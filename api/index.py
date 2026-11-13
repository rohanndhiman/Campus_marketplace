import sys
import os

# Ensure the root directory is on the path so app can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from flask import redirect, url_for

class VercelPathMiddleware:
    """Fixes PATH_INFO when Vercel rewrites requests to /api/index."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = environ.get('HTTP_X_MATCHED_PATH') or environ.get('REQUEST_URI')
        if matched_path:
            clean_path = matched_path.split('?')[0]
            if clean_path in ('/api/index', '/api/index.py'):
                clean_path = '/'
            environ['PATH_INFO'] = clean_path
        elif environ.get('PATH_INFO') in ('/api/index', '/api/index.py'):
            environ['PATH_INFO'] = '/'
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

@app.route('/api/index')
def vercel_api_index():
    return redirect(url_for('index'))
