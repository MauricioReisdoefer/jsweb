import asyncio
import os
import secrets

from .auth import get_current_user, init_auth
from .blueprints import Blueprint
from .middleware import CSRFMiddleware, DBSessionMiddleware, StaticFilesMiddleware
from .request import Request
from .response import HTMLResponse, JSONResponse, Response, configure_template_env
from .routing import MethodNotAllowed, NotFound, Router


class JsWebApp:
    """
    The main application class for the JsWeb framework.

    This class is the central object in a JsWeb application. It is used to
    configure routes, register blueprints, and handle the ASGI application
    lifecycle.

    Attributes:
        router (Router): The application's router instance.
        config (object): A configuration object with application settings.
        blueprints_with_static_files (list): A list of blueprints that have static files.
    """

    def __init__(self, config):
        """
        Initializes the JsWebApp instance.

        Args:
            config: A configuration object or module containing settings like
                    SECRET_KEY, TEMPLATE_FOLDER, etc.
        """
        self.router = Router()
        self.template_filters = {}
        self.config = config
        self.blueprints_with_static_files = []
        self._init_from_config()

    def _init_from_config(self):
        """
        Initializes components that depend on the application's configuration.

        This internal method sets up the template environment and authentication
        system based on the provided config.
        """
        template_paths = []

        if hasattr(self.config, "TEMPLATE_FOLDER") and hasattr(self.config, "BASE_DIR"):
            user_template_path = os.path.join(self.config.BASE_DIR, self.config.TEMPLATE_FOLDER)
            if os.path.isdir(user_template_path):
                template_paths.append(user_template_path)

        lib_template_path = os.path.join(os.path.dirname(__file__), "templates")
        if os.path.isdir(lib_template_path):
            template_paths.append(lib_template_path)

        if template_paths:
            configure_template_env(template_paths)

        if hasattr(self.config, "SECRET_KEY"):
            init_auth(self.config.SECRET_KEY, self._get_actual_user_loader())

    def _get_actual_user_loader(self):
        """
        Retrieves the user loader callback function.

        This method is used internally to find the correct function for loading a
        user from an ID, which is essential for the authentication system.

        Returns:
            The user loader function.
        """
        if hasattr(self, '_user_loader_callback') and self._user_loader_callback:
            return self._user_loader_callback
        return self.user_loader

    def user_loader(self, user_id: int):
        """
        Default user loader that loads a user by their ID.

        This default implementation attempts to import a `User` model from a `models`
        module in the user's project and query it by ID. This method can be
        overridden with a custom loader using the `@app.user_loader` decorator.

        Args:
            user_id (int): The ID of the user to load.

        Returns:
            The User object if found, otherwise None.
        """
        try:
            from models import User
            return User.query.get(user_id)
        except (ImportError, AttributeError):
            return None

    def route(self, path, methods=None, endpoint=None):
        """
        A decorator to register a new route and associate it with a view function.

        Args:
            path (str): The URL path for the route (e.g., '/users/<int:id>').
            methods (list, optional): A list of allowed HTTP methods (e.g., ['GET', 'POST']).
                                      Defaults to ['GET'].
            endpoint (str, optional): A unique name for the route. If not provided,
                                      the name of the view function is used.

        Returns:
            The decorator function.
        """
        return self.router.route(path, methods, endpoint)

    def register_blueprint(self, blueprint: Blueprint):
        """
        Registers a blueprint with the application.

        This method iterates over the routes defined in the blueprint and adds them
        to the application's router, optionally prefixing them with the blueprint's
        `url_prefix`. It also registers the blueprint's static file directory if one is defined.

        Args:
            blueprint (Blueprint): The Blueprint instance to register.
        """
        for path, handler, methods, endpoint in blueprint.routes:
            full_path = path
            if blueprint.url_prefix:
                full_path = f"{blueprint.url_prefix.rstrip('/')}/{path.lstrip('/')}"

            full_endpoint = f"{blueprint.name}.{endpoint}"
            self.router.add_route(full_path, handler, methods, endpoint=full_endpoint)

        if blueprint.static_folder:
            self.blueprints_with_static_files.append(blueprint)

    def filter(self, name):
        """
        A decorator to register a custom template filter.

        The decorated function will be available in Jinja2 templates by the given name.

        Args:
            name (str): The name of the filter to use in templates.

        Returns:
            The decorator function.
        """

        def decorator(func):
            self.template_filters[name] = func
            return func

        return decorator

    async def _asgi_app_handler(self, scope, receive, send):
        """
        Internal ASGI handler for processing a single request.

        This method resolves the route, calls the appropriate handler, and sends
        the response. It handles exceptions like `NotFound` and `MethodNotAllowed`.

        Args:
            scope: The ASGI scope for the request.
            receive: The ASGI receive channel.
            send: The ASGI send channel.
        """
        req = scope['jsweb.request']
        try:
            handler, params = self.router.resolve(req.path, req.method)
        except NotFound as e:
            response = JSONResponse({"error": str(e)}, status_code=404)
            await response(scope, receive, send)
            return
        except MethodNotAllowed as e:
            response = JSONResponse({"error": str(e)}, status_code=405)
            await response(scope, receive, send)
            return
        except Exception:
            response = JSONResponse({"error": "Internal Server Error"}, status_code=500)
            await response(scope, receive, send)
            return

        if handler:
            if asyncio.iscoroutinefunction(handler):
                response = await handler(req, **params)
            else:
                response = handler(req, **params)

            if isinstance(response, str):
                response = HTMLResponse(response)

            if not isinstance(response, Response):
                raise TypeError(f"View function did not return a Response object (got {type(response).__name__})")

        if hasattr(req, 'new_csrf_token_generated') and req.new_csrf_token_generated:
            response.set_cookie("csrf_token", req.csrf_token, httponly=False, samesite='Lax')

        await response(scope, receive, send)

    async def __call__(self, scope, receive, send):
        """
        The main ASGI application entry point.

        This method is called by the ASGI server for each request. It sets up the
        request object, wraps the main handler with middleware, and processes the request.

        Args:
            scope: The ASGI scope for the request.
            receive: The ASGI receive channel.
            send: The ASGI send channel.
        """
        if scope["type"] != "http":
            return

        req = Request(scope, receive, self)
        scope['jsweb.request'] = req

        csrf_token = req.cookies.get("csrf_token")
        req.new_csrf_token_generated = False
        if not csrf_token:
            csrf_token = secrets.token_hex(32)
            req.new_csrf_token_generated = True
        req.csrf_token = csrf_token

        if hasattr(self.config, "SECRET_KEY"):
            req.user = get_current_user(req)

        static_url = getattr(self.config, "STATIC_URL", "/static")
        static_dir = getattr(self.config, "STATIC_DIR", "static")

        handler = self._asgi_app_handler
        handler = DBSessionMiddleware(handler)
        handler = StaticFilesMiddleware(handler, static_url, static_dir,
                                        blueprint_statics=self.blueprints_with_static_files)
        handler = CSRFMiddleware(handler)

        await handler(scope, receive, send)
