# D:/jones/Python/jsweb/jsweb/response.py
import json as pyjson
from typing import List, Tuple, Union

# ✅ 1. Create a mapping of common status codes to their reason phrases.
HTTP_STATUS_CODES = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
}


class Response:
    """
    A base class for HTTP responses. It encapsulates the body, status, and headers.
    """
    default_content_type = "text/plain"

    def __init__(
            self,
            body: Union[str, bytes],
            # ✅ 2. Allow status to be an integer or a string for user convenience.
            status: Union[int, str] = 200,
            headers: List[Tuple[str, str]] = None,
            content_type: str = None,
    ):
        self.body = body

        # ✅ 3. Smartly handle the status code.
        if isinstance(status, int):
            # If an integer is passed, look up the reason phrase and build the full status string.
            reason = HTTP_STATUS_CODES.get(status, "Unknown Status")
            self.status = f"{status} {reason}"
        else:
            # If a full string is passed, use it directly.
            self.status = status

        self.headers = list(headers) if headers else []

        # Set the content type, avoiding duplicates
        final_content_type = content_type or self.default_content_type
        if not any(h[0].lower() == "content-type" for h in self.headers):
            self.headers.append(("Content-Type", final_content_type))

    def to_wsgi(self) -> Tuple[bytes, str, List[Tuple[str, str]]]:
        """
        Converts the Response object into a tuple that the WSGI server can understand.
        """
        body_bytes = self.body if isinstance(self.body, bytes) else self.body.encode("utf-8")
        return body_bytes, self.status, self.headers


class HTMLResponse(Response):
    """
    A specific response class for HTML content.
    """
    default_content_type = "text/html"


class JSONResponse(Response):
    """
    A specific response class for JSON content.
    It automatically handles dumping the data to a JSON string.
    """
    default_content_type = "application/json"

    def __init__(
            self,
            data: any,
            # ✅ This now also accepts integers.
            status: Union[int, str] = 200,
            headers: List[Tuple[str, str]] = None,
    ):
        body = pyjson.dumps(data)
        # The parent __init__ will handle the status code conversion automatically.
        super().__init__(body, status, headers)


# The helper functions now automatically support integer status codes
# because they pass the status directly to the Response classes.
def html(body: str, status: Union[int, str] = 200, headers: List[Tuple[str, str]] = None) -> HTMLResponse:
    """Helper function to quickly create an HTMLResponse."""
    return HTMLResponse(body, status, headers)


def json(data: any, status: Union[int, str] = 200, headers: List[Tuple[str, str]] = None) -> JSONResponse:
    """Helper function to quickly create a JSONResponse."""
    return JSONResponse(data, status, headers)