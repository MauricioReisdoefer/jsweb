import re


class NotFound(Exception):
    """
    Raised when a route is not found.
    """
    pass


class MethodNotAllowed(Exception):
    """
    Raised when a method is not allowed for a route.
    """
    pass


class Route:
    """
    Represents a single route with path, handler, and parameter conversion.
    """
    def __init__(self, path, handler, methods, endpoint):
        self.path = path
        self.handler = handler
        self.methods = methods
        self.endpoint = endpoint
        self.converters = {}
        self.regex, self.param_names = self._compile_path()

    def _compile_path(self):
        """
        Compiles the path into a regex and extracts parameter converters.
        """
        type_converters = {
            'str': (str, r'[^/]+'),
            'int': (int, r'\d+'),
            'path': (str, r'.+?')
        }
        
        param_defs = re.findall(r"<(\w+):(\w+)>", self.path)
        regex_path = "^" + self.path + "$"
        param_names = []

        for type_name, param_name in param_defs:
            converter, regex_part = type_converters.get(type_name, type_converters['str'])
            regex_path = regex_path.replace(f"<{type_name}:{param_name}>", f"(?P<{param_name}>{regex_part})")
            self.converters[param_name] = converter
            param_names.append(param_name)

        return re.compile(regex_path), param_names

    def match(self, path):
        """
        Matches the given path against the route's regex and returns converted parameters.
        """
        match = self.regex.match(path)
        if not match:
            return None

        params = match.groupdict()
        try:
            for name, value in params.items():
                params[name] = self.converters[name](value)
            return params
        except ValueError:
            return None


class Router:
    """
    Handles routing by mapping URL paths to view functions and endpoint names.
    """
    def __init__(self):
        self.routes = []
        self.endpoints = {}  # For reverse lookups (url_for)
        self.static_url_path = None
        self.static_dir = None

    def add_static_route(self, url_path, directory):
        """
        Adds a route for serving static files.
        """
        self.static_url_path = url_path
        self.static_dir = directory
        
        # Simple handler for serving static files
        def static_handler(filename):
            import os
            from werkzeug.exceptions import NotFound
            
            # Basic security check
            if '..' in filename or filename.startswith('/'):
                raise NotFound()

            file_path = os.path.join(self.static_dir, filename)
            if os.path.isfile(file_path):
                # In a real app, you would return a proper file response here.
                # For now, we'll just indicate success.
                return f"Serving {file_path}"
            raise NotFound()

        self.add_route(f"{url_path}/<path:filename>", static_handler, endpoint="static")

    def add_route(self, path, handler, methods=None, endpoint=None):
        """
        Adds a new route to the router.
        """
        if methods is None:
            methods = ["GET"]
        
        if endpoint is None:
            endpoint = handler.__name__

        if endpoint in self.endpoints:
            raise ValueError(f"Endpoint \"{endpoint}\" is already registered.")

        route = Route(path, handler, methods, endpoint)
        self.routes.append(route)
        self.endpoints[endpoint] = route

    def route(self, path, methods=None, endpoint=None):
        """
        A decorator to register a view function for a given URL path.
        """
        def decorator(handler):
            self.add_route(path, handler, methods, endpoint)
            return handler
        return decorator

    def resolve(self, path, method):
        """
        Finds the appropriate handler for a given path and HTTP method.
        """
        for route in self.routes:
            params = route.match(path)
            if params is not None:
                if method in route.methods:
                    return route.handler, params
                else:
                    raise MethodNotAllowed
        raise NotFound

    def url_for(self, endpoint, **params):
        """
        Generates a URL for a given endpoint and parameters.
        """
        if endpoint not in self.endpoints:
            raise ValueError(f"No route found for endpoint '{endpoint}'.")

        route = self.endpoints[endpoint]
        path = route.path

        for param_name in route.param_names:
            if param_name not in params:
                raise ValueError(f"Missing parameter '{param_name}' for endpoint '{endpoint}'.")
            
            # This is a simplified replacement. For a full implementation,
            # you'd need to handle the <type:name> format more robustly.
            # For this example, we assume simple string replacement.
            path = re.sub(r"<(\w+):" + param_name + ">", str(params[param_name]), path)

        # Handle any remaining simple path variables like '<id>'
        for key, value in params.items():
            path = path.replace(f"<{key}>", str(value))
        
        return path
