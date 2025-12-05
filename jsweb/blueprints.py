class Blueprint:
    """
    A self-contained, reusable component of a JsWeb application.
    Blueprints have their own routes which are later registered with the main app.
    """
    def __init__(self, name, url_prefix=None):
        """
        Initializes a new Blueprint.

        Args:
            name (str): The name of the blueprint.
            url_prefix (str, optional): A prefix to be added to all routes in this blueprint.
        """
        self.name = name
        self.url_prefix = url_prefix
        self.routes = []

    def add_route(self, path, handler, methods=None, endpoint=None):
        """
        Programmatically adds a route to the blueprint. This is useful for
        dynamically generated views, like in the admin panel.
        """
        if methods is None:
            methods = ["GET"]
        
        # If no endpoint is provided, use the function name as the default.
        route_endpoint = endpoint or handler.__name__
        self.routes.append((path, handler, methods, route_endpoint))

    def route(self, path, methods=None, endpoint=None):
        """
        A decorator to register a view function for a given path within the blueprint.
        """
        def decorator(handler):
            self.add_route(path, handler, methods, endpoint)
            return handler
        return decorator
