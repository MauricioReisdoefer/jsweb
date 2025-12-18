import secrets
import logging
from .static import serve_static
from .response import Forbidden
import json

logger = logging.getLogger(__name__)

class Middleware:
    """
    Base class for ASGI middleware.

    Args:
        app: The ASGI application to wrap.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        """
        The ASGI application interface.

        Args:
            scope (dict): The ASGI connection scope.
            receive (callable): An awaitable callable to receive events.
            send (callable): An awaitable callable to send events.
        """
        await self.app(scope, receive, send)

class CSRFMiddleware(Middleware):
    """
    Middleware to protect against Cross-Site Request Forgery (CSRF) attacks.

    This middleware enforces CSRF protection for all state-changing HTTP methods
    (POST, PUT, PATCH, DELETE). It requires a valid CSRF token to be present
    in the request, either in the 'X-CSRF-Token' header or in the request body
    (JSON or Form Data).
    """
    async def __call__(self, scope, receive, send):
        """
        Validates the CSRF token for state-changing HTTP methods.

        If validation fails, it returns a 403 Forbidden response. Otherwise, it
        passes the request to the next application in the stack.

        Args:
            scope (dict): The ASGI connection scope.
            receive (callable): An awaitable callable to receive events.
            send (callable): An awaitable callable to send events.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        req = scope['jsweb.request']

        if req.method in ("POST", "PUT", "PATCH", "DELETE"):
            cookie_token = req.cookies.get("csrf_token")
            submitted_token = None

            # 1. Check header first (Best practice for AJAX/APIs)
            submitted_token = req.headers.get("x-csrf-token")

            # 2. If no header token, check the body based on content type
            if not submitted_token:
                content_type = req.headers.get("content-type", "")
                
                if "application/json" in content_type:
                    try:
                        # Request.json() safely returns {} for empty/invalid bodies
                        data = await req.json()
                        submitted_token = data.get("csrf_token")
                    except Exception:
                        # If JSON parsing fails, we treat it as no token found
                        pass
                
                elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                    try:
                        # Request.form() safely returns {} for empty/non-form bodies
                        form = await req.form()
                        submitted_token = form.get("csrf_token")
                    except Exception:
                        # If form parsing fails, we treat it as no token found
                        pass

            # 3. Perform the validation
            # Both the cookie token and the submitted token MUST be present and match.
            if not cookie_token or not submitted_token or not secrets.compare_digest(submitted_token, cookie_token):
                logger.warning(
                    f"CSRF validation failed for {req.method} {req.path}. "
                    f"Cookie set: {'Yes' if cookie_token else 'No'}, "
                    f"Token submitted: {'Yes' if submitted_token else 'No'}."
                )
                response = Forbidden("CSRF token missing or invalid.")
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

class StaticFilesMiddleware(Middleware):
    """
    Middleware for serving static files.

    It intercepts requests that match the configured static URL paths for the main app
    and any registered blueprints, and serves the corresponding file if found.

    Args:
        app: The ASGI application to wrap.
        static_url (str): The URL prefix for the main application's static files.
        static_dir (str): The directory path for the main application's static files.
        blueprint_statics (list, optional): A list of blueprint static file configurations.
    """
    def __init__(self, app, static_url, static_dir, blueprint_statics=None):
        super().__init__(app)
        self.static_url = static_url
        self.static_dir = static_dir
        self.blueprint_statics = blueprint_statics or []

    async def __call__(self, scope, receive, send):
        """
        Handles requests for static files.

        It checks if the request path matches any of the static file URL prefixes.
        If a match is found, it attempts to serve the file. Otherwise, it passes
        the request to the next application.

        Args:
            scope (dict): The ASGI connection scope.
            receive (callable): An awaitable callable to receive events.
            send (callable): An awaitable callable to send events.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        req = scope['jsweb.request']

        # Check blueprint static files first
        for bp in self.blueprint_statics:
            if bp.static_url_path and req.path.startswith(bp.static_url_path):
                response = serve_static(req.path, bp.static_url_path, bp.static_folder)
                await response(scope, receive, send)
                return

        # Fallback to main static files
        if req.path.startswith(self.static_url):
            response = serve_static(req.path, self.static_url, self.static_dir)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

class DBSessionMiddleware(Middleware):
    """
    Manages the lifecycle of a database session for each HTTP request.

    This middleware ensures that a SQLAlchemy session is properly handled. It commits
    the transaction if the request is successful, rolls it back upon an exception,
    and always removes the session at the end of the request.
    """
    async def __call__(self, scope, receive, send):
        """
        Wraps the request with a database session scope.

        Args:
            scope (dict): The ASGI connection scope.
            receive (callable): An awaitable callable to receive events.
            send (callable): An awaitable callable to send events.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        from .database import db_session
        try:
            await self.app(scope, receive, send)
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise
        finally:
            db_session.remove()
