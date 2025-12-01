from urllib.parse import parse_qs
import json
from io import BytesIO
from werkzeug.formparser import parse_form_data
from werkzeug.datastructures import FileStorage

class Request:
    def __init__(self, environ, app):
        self.environ = environ
        self.app = app  # Store a reference to the app instance
        self.method = self.environ.get("REQUEST_METHOD", "GET").upper()
        self.path = self.environ.get("PATH_INFO", "/")
        self.query = self._parse_query(self.environ.get("QUERY_STRING", ""))
        self.headers = self._parse_headers(self.environ)
        self.cookies = self._parse_cookies(self.environ)
        self.user = None  # Will be populated by the app

        self._body = None
        self._form = None
        self._json = None
        self._files = None

    @property
    def body(self):
        if self._body is None:
            try:
                length = int(self.environ.get("CONTENT_LENGTH", 0))
                self._body = self.environ["wsgi.input"].read(length).decode("utf-8")
            except (ValueError, KeyError):
                self._body = ""
        return self._body

    @property
    def json(self):
        """Parse JSON request body."""
        if self._json is None:
            content_type = self.environ.get("CONTENT_TYPE", "")
            if "application/json" in content_type:
                try:
                    self._json = json.loads(self.body) if self.body else {}
                except (json.JSONDecodeError, ValueError):
                    self._json = {}
            else:
                self._json = {}
        return self._json

    @property
    def form(self):
        if self._form is None:
            content_type = self.environ.get("CONTENT_TYPE", "")
            if self.method in ("POST", "PUT", "PATCH"):
                if "application/x-www-form-urlencoded" in content_type:
                    self._form = {k: v[0] for k, v in parse_qs(self.body).items()}
                elif "multipart/form-data" in content_type:
                    # Parse multipart form data
                    self._parse_multipart()
                else:
                    self._form = {}
            else:
                self._form = {}
        return self._form

    @property
    def files(self):
        """Access uploaded files from multipart/form-data requests."""
        if self._files is None:
            content_type = self.environ.get("CONTENT_TYPE", "")
            if self.method in ("POST", "PUT", "PATCH") and "multipart/form-data" in content_type:
                self._parse_multipart()
            else:
                self._files = {}
        return self._files

    def _parse_query(self, query_string):
        return {k: v[0] for k, v in parse_qs(query_string).items()}

    def _parse_headers(self, environ):
        return {
            k[5:].replace("_", "-").title(): v
            for k, v in environ.items()
            if k.startswith("HTTP_")
        }

    def _parse_cookies(self, environ):
        cookie_string = environ.get("HTTP_COOKIE", "")
        if not cookie_string:
            return {}
        cookies = {}
        for cookie in cookie_string.split('; '):
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key] = value
        return cookies

    def _parse_multipart(self):
        """Parse multipart/form-data for forms and file uploads."""
        if self._form is not None and self._files is not None:
            return  # Already parsed

        self._form = {}
        self._files = {}

        try:
            # parse multipart data
            stream, form_data, files = parse_form_data(self.environ)

            # Convert form data to dict
            for key in form_data.keys():
                values = form_data.getlist(key)
                if len(values) == 1:
                    self._form[key] = values[0]
                else:
                    self._form[key] = values

            # Convert files to UploadedFile objects
            for key in files.keys():
                file_list = files.getlist(key)
                if len(file_list) == 1:
                    self._files[key] = UploadedFile(file_list[0])
                else:
                    self._files[key] = [UploadedFile(f) for f in file_list]

        except Exception:
            # If parsing fails, initialize empty dicts
            self._form = {}
            self._files = {}


class UploadedFile:
    """Represents an uploaded file."""

    def __init__(self, file_storage):
        """
        Initialize from a werkzeug FileStorage object.

        Args:
            file_storage: werkzeug.datastructures.FileStorage object
        """
        self.filename = file_storage.filename
        self.name = file_storage.name
        self.content_type = file_storage.content_type
        self.stream = file_storage.stream
        self._content = None

    def read(self):
        """Read the file content."""
        if self._content is None:
            self.stream.seek(0)
            self._content = self.stream.read()
        return self._content

    def save(self, destination):
        """Save the uploaded file to a destination path."""
        with open(destination, 'wb') as f:
            f.write(self.read())

    @property
    def size(self):
        """Get the size of the uploaded file in bytes."""
        content = self.read()
        return len(content) if content else 0

    def __repr__(self):
        return f"<UploadedFile: {self.filename} ({self.content_type})>"
