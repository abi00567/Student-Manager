import os
import sys

# Add project root directory to sys.path so 'app' package can be imported
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.app import app


class StripPrefixMiddleware:
    """
    Middleware that strips /api/index or /api prefixes so routes match correctly
    whether requested directly or via Vercel rewrites.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path.startswith("/api/index"):
            environ["PATH_INFO"] = path[len("/api/index"):] or "/"
        elif path.startswith("/api"):
            environ["PATH_INFO"] = path[len("/api"):] or "/"
        return self.wsgi_app(environ, start_response)


# Apply middleware to Flask's WSGI pipeline
app.wsgi_app = StripPrefixMiddleware(app.wsgi_app)
