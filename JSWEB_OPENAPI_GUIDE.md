# jsweb OpenAPI Documentation System

**Fast, secure, automatic API documentation with NestJS-style control**

## 🎯 Overview

The jsweb OpenAPI system provides **automatic API documentation and validation**, just like FastAPI, with zero configuration needed!

✅ **Automatic on `jsweb run`** - Docs available at `/docs` immediately
✅ **Automatic Validation** - Request bodies validated with Pydantic v2
✅ **Hybrid Architecture** - Pydantic internally, clean jsweb API externally
✅ **NestJS-Style Decorators** - Fine-grained control when needed
✅ **Multiple UIs** - Swagger UI, ReDoc, and RapiDoc support
✅ **Zero Boilerplate** - Works out of the box

---

## 🚀 Quick Start (3 Steps)

### 1. Create a New Project

```bash
jsweb new my-api
cd my-api
```

### 2. Define Your API with DTOs

```python
# views.py
from jsweb import Blueprint, json
from jsweb.dto import JswebBaseModel, Field, validator
from jsweb.docs import (
    api_operation,
    api_response,
    api_body,
    api_query,
    api_tags
)

# Define DTOs
class UserDto(JswebBaseModel):
    id: int = Field(description="User ID", example=1)
    name: str = Field(
        description="User's full name",
        min_length=1,
        max_length=100,
        example="John Doe"
    )
    email: str = Field(
        description="Email address",
        pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$',
        example="john@example.com"
    )
    age: int = Field(
        ge=0,
        le=150,
        description="User's age in years",
        example=30
    )

class CreateUserDto(JswebBaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(ge=0, le=150)

    @validator('email')
    @classmethod
    def validate_email(cls, value):
        """Normalize email to lowercase."""
        return value.lower()

# Create Blueprint
views_bp = Blueprint('views')

# Document Your Routes
@views_bp.route("/api/users", methods=["GET"])
@api_tags("Users")
@api_operation(
    summary="List all users",
    description="Returns a paginated list of all users"
)
@api_query('page', type=int, description="Page number", example=1)
@api_query('limit', type=int, description="Items per page", example=10)
@api_response(200, UserDto, description="List of users")
async def list_users(req):
    """Get all users with optional pagination."""
    users = [
        {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25}
    ]
    return json({"users": users})

@views_bp.route("/api/users", methods=["POST"])
@api_tags("Users")
@api_operation(summary="Create new user")
@api_body(CreateUserDto)  # ⚡ AUTOMATIC VALIDATION!
@api_response(201, UserDto, description="User created")
@api_response(400, description="Validation error")
async def create_user(req):
    """Create a new user with automatic validation."""
    # ✅ Request is automatically validated
    # ✅ req.validated_body = CreateUserDto instance
    # ✅ req.validated_data = dict representation

    user_data = req.validated_data
    new_user = {"id": 3, **user_data}
    return json(new_user, status=201)
```

### 3. Run Your App

```bash
jsweb run
```

**That's it!** Visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## ⚡ Automatic Features

### 🔄 **Automatic on `jsweb run`**

When you run `jsweb run`, OpenAPI docs are **automatically enabled**:

```bash
$ jsweb run

[*] OpenAPI documentation enabled:
   > Swagger UI: /docs
   > ReDoc:      /redoc
   > JSON spec:  /openapi.json

[*] JsWeb server running on http://127.0.0.1:8000
[*] Press Ctrl+C to stop the server
```

**No manual setup required!** The docs are immediately available.

---

### ✅ **Automatic Request Validation**

When you use `@api_body()`, validation happens automatically:

```python
@api_body(CreateUserDto)  # Validation enabled by default!
async def create_user(req):
    # Request body is automatically validated
    user_data = req.validated_data
    return json(user_data)
```

**Valid Request:**
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com", "age": 30}'
```

**Response:** ✅ 201 Created

**Invalid Request:**
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "", "email": "invalid", "age": -5}'
```

**Response:** ❌ 400 Bad Request (Automatic!)
```json
{
  "error": "Validation failed",
  "details": [
    {
      "field": "name",
      "message": "String should have at least 1 character",
      "type": "string_too_short"
    },
    {
      "field": "email",
      "message": "String should match pattern '^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$'",
      "type": "string_pattern_mismatch"
    },
    {
      "field": "age",
      "message": "Input should be greater than or equal to 0",
      "type": "greater_than_equal"
    }
  ]
}
```

---

## 🔧 Configuration

OpenAPI docs are configured via your `config.py` file:

```python
# config.py (auto-generated in new projects)

# OpenAPI / Swagger Documentation (Automatic!)
# Docs are automatically available at /docs, /redoc, and /openapi.json
# Set ENABLE_OPENAPI_DOCS = False to disable
ENABLE_OPENAPI_DOCS = True           # Enable automatic API documentation
API_TITLE = "My API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "My awesome API built with jsweb"
OPENAPI_DOCS_URL = "/docs"           # Swagger UI URL
OPENAPI_REDOC_URL = "/redoc"         # ReDoc UI URL
OPENAPI_JSON_URL = "/openapi.json"   # OpenAPI spec JSON URL
```

### Customizing Documentation

```python
# config.py
API_TITLE = "User Management API"
API_VERSION = "2.0.0"
API_DESCRIPTION = """
# User Management API

A comprehensive API for managing users.

## Features

- CRUD operations
- Automatic validation
- JWT authentication
- Rate limiting
"""
```

### Changing URLs

```python
# config.py
OPENAPI_DOCS_URL = "/api-docs"        # Swagger UI at /api-docs
OPENAPI_REDOC_URL = "/documentation"  # ReDoc at /documentation
OPENAPI_JSON_URL = "/api/schema"      # JSON spec at /api/schema
```

### Disabling Docs

```python
# config.py
ENABLE_OPENAPI_DOCS = False  # Completely disable OpenAPI docs
```

---

## 📚 Complete API Reference

### DTO System

#### `JswebBaseModel`

Base class for all DTOs. Uses Pydantic v2 internally but exposes jsweb API.

```python
from jsweb.dto import JswebBaseModel, Field

class MyDto(JswebBaseModel):
    field1: str = Field(description="...")
    field2: int = Field(ge=0, description="...")
```

**Methods:**
- `openapi_schema()` - Get OpenAPI schema
- `from_dict(data)` - Create from dict with validation
- `to_dict()` - Convert to dict
- `to_json()` - Convert to JSON string

#### `Field()`

Define a field with validation and OpenAPI metadata.

```python
Field(
    default=...,              # Default value (... = required)

    # Validation
    gt=None,                  # Greater than
    ge=None,                  # Greater than or equal
    lt=None,                  # Less than
    le=None,                  # Less than or equal
    multiple_of=None,         # Must be multiple of
    min_length=None,          # Min length (str/list)
    max_length=None,          # Max length (str/list)
    pattern=None,             # Regex pattern

    # OpenAPI metadata
    title=None,               # Field title
    description=None,         # Field description
    example=None,             # Example value
    examples=None,            # Multiple examples
    deprecated=False,         # Mark as deprecated

    # Field behavior
    alias=None,               # Alternative name
    default_factory=None,     # Factory for default
)
```

**Examples:**

```python
# String with constraints
name: str = Field(
    description="User name",
    min_length=1,
    max_length=100,
    example="John Doe"
)

# Integer with range
age: int = Field(
    ge=0,
    le=150,
    description="Age in years",
    example=30
)

# Email with pattern
email: str = Field(
    pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$',
    description="Email address"
)

# Optional field with default
status: str = Field(
    default="active",
    description="User status"
)

# List field
tags: List[str] = Field(
    default_factory=list,
    description="User tags"
)
```

#### Validators

```python
from jsweb.dto import validator, root_validator

class UserDto(JswebBaseModel):
    email: str
    password: str
    confirm_password: str

    @validator('email')
    @classmethod
    def validate_email(cls, value):
        if '@' not in value:
            raise ValueError('Invalid email')
        return value.lower()  # Normalize

    @root_validator()
    @classmethod
    def validate_passwords_match(cls, values):
        if values['password'] != values['confirm_password']:
            raise ValueError('Passwords do not match')
        return values
```

---

### Documentation Decorators

#### `@api_operation()`

Document an API operation.

```python
@api_operation(
    summary="Short description",
    description="Detailed description",
    operation_id="unique_operation_id",
    deprecated=False
)
```

#### `@api_response()`

Document a response.

```python
@api_response(
    status_code=200,
    dto=UserDto,
    description="Success response",
    content_type="application/json",
    examples={...}
)
```

**Multiple responses:**

```python
@api_response(200, UserDto, "User found")
@api_response(404, ErrorDto, "Not found")
@api_response(400, ErrorDto, "Bad request")
async def get_user(req, user_id):
    ...
```

#### `@api_body()` ⚡ **With Automatic Validation**

Document request body with **built-in validation**.

```python
@api_body(
    dto=CreateUserDto,
    description="Request body description",
    content_type="application/json",
    required=True,
    auto_validate=True  # ✅ Default: automatic validation enabled
)
```

**Example:**

```python
@api_bp.route("/users", methods=["POST"])
@api_body(CreateUserDto)  # Automatic validation!
@api_response(201, UserDto)
async def create_user(req):
    # req.validated_body = CreateUserDto instance
    # req.validated_data = dict
    user_data = req.validated_data
    return json({"user": user_data}, status=201)
```

**Disable validation if needed:**

```python
@api_body(CreateUserDto, auto_validate=False)
async def create_user_manual(req):
    data = await req.json()  # Manual handling
    return json(data)
```

#### `@api_query()`

Document query parameters.

```python
@api_query(
    name='page',
    type=int,
    required=False,
    description="Page number",
    example=1
)
```

**Multiple query params:**

```python
@api_query('page', type=int, description="Page number", example=1)
@api_query('limit', type=int, description="Items per page", example=10)
@api_query('search', type=str, description="Search query")
async def list_items(req):
    ...
```

#### `@api_header()`

Document header parameters.

```python
@api_header(
    name='X-API-Key',
    required=True,
    description="API key for authentication"
)
```

#### `@api_tags()`

Add tags for grouping.

```python
@api_tags("Users", "Admin")
async def admin_user_route(req):
    ...
```

#### `@api_security()`

Apply security requirements.

```python
@api_security("bearer_auth")
async def protected_route(req):
    ...

# OAuth2 with scopes
@api_security("oauth2", scopes=["read:users", "write:users"])
async def oauth_route(req):
    ...
```

---

### Utilities

#### `disable_auto_validation()`

Disable automatic validation for a specific route.

```python
from jsweb.docs import disable_auto_validation

@api_body(CreateUserDto)
@disable_auto_validation
async def create_user(req):
    # Validation is skipped, but docs still generated
    data = await req.json()  # Manual handling
    return json(data)
```

---

## 🎨 Advanced Examples

### Example 1: CRUD API with Full Documentation

```python
from jsweb import Blueprint, json
from jsweb.dto import JswebBaseModel, Field, validator
from jsweb.docs import *

# DTOs
class TodoDto(JswebBaseModel):
    id: int = Field(description="Todo ID")
    title: str = Field(description="Todo title", max_length=200)
    completed: bool = Field(description="Completion status", example=False)
    priority: int = Field(ge=1, le=5, description="Priority (1-5)", example=3)

class CreateTodoDto(JswebBaseModel):
    title: str = Field(min_length=1, max_length=200)
    priority: int = Field(ge=1, le=5, default=3)

    @validator('title')
    @classmethod
    def validate_title(cls, value):
        if value.strip() == '':
            raise ValueError('Title cannot be empty')
        return value.strip()

class UpdateTodoDto(JswebBaseModel):
    title: Optional[str] = Field(None, max_length=200)
    completed: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=5)

# Blueprint
todos_bp = Blueprint('todos', url_prefix='/api/todos')

@todos_bp.route("", methods=["GET"])
@api_tags("Todos")
@api_operation(summary="List todos")
@api_query('completed', type=bool, description="Filter by completion status")
@api_response(200, TodoDto, description="List of todos")
async def list_todos(req):
    return json({"todos": []})

@todos_bp.route("/<int:todo_id>", methods=["GET"])
@api_tags("Todos")
@api_operation(summary="Get todo by ID")
@api_response(200, TodoDto)
@api_response(404, ErrorDto)
async def get_todo(req, todo_id):
    return json({"id": todo_id, "title": "Sample", "completed": False, "priority": 3})

@todos_bp.route("", methods=["POST"])
@api_tags("Todos")
@api_operation(summary="Create todo")
@api_body(CreateTodoDto)  # ⚡ Automatic validation!
@api_response(201, TodoDto)
@api_response(400, ErrorDto)
async def create_todo(req):
    todo_data = req.validated_data  # Already validated!
    return json({"id": 1, **todo_data}, status=201)

@todos_bp.route("/<int:todo_id>", methods=["PATCH"])
@api_tags("Todos")
@api_operation(summary="Update todo")
@api_body(UpdateTodoDto)  # ⚡ Automatic validation!
@api_response(200, TodoDto)
async def update_todo(req, todo_id):
    updates = req.validated_data
    todo = {"id": todo_id, "title": "Sample", "completed": False, "priority": 3}
    todo.update(updates)
    return json(todo)

@todos_bp.route("/<int:todo_id>", methods=["DELETE"])
@api_tags("Todos")
@api_operation(summary="Delete todo")
@api_response(204, description="Deleted")
@api_response(404, ErrorDto)
async def delete_todo(req, todo_id):
    return json(None, status=204)
```

### Example 2: Protected Routes with Authentication

```python
from jsweb.docs import api_security, add_security_scheme
from jsweb.docs import openapi_registry

# Register security scheme (in app.py or views.py)
openapi_registry.add_security_scheme("bearer_auth", {
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "JWT"
})

@api.route("/profile", methods=["GET"])
@api_tags("Users")
@api_operation(summary="Get current user profile")
@api_security("bearer_auth")
@api_header('Authorization', required=True, description="Bearer token")
@api_response(200, UserDto)
@api_response(401, ErrorDto, "Unauthorized")
async def get_profile(req):
    token = req.headers.get('Authorization')
    return json({"user": {...}})
```

### Example 3: File Upload

```python
class FileUploadDto(JswebBaseModel):
    filename: str = Field(description="File name")
    size: int = Field(description="File size in bytes")
    content_type: str = Field(description="MIME type")

@api.route("/upload", methods=["POST"])
@api_tags("Files")
@api_operation(summary="Upload file")
@api_body(
    dto=FileUploadDto,
    content_type="multipart/form-data",
    description="File upload"
)
@api_response(200, FileUploadDto)
async def upload_file(req):
    files = await req.files()
    return json({"filename": "...", "size": 1024, "content_type": "image/png"})
```

---

## 🔐 Security Best Practices

### JWT Authentication

```python
from jsweb.docs import openapi_registry

openapi_registry.add_security_scheme("bearer_auth", {
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "JWT",
    "description": "Enter your JWT token"
})

@api_security("bearer_auth")
async def protected_route(req):
    ...
```

### API Key

```python
openapi_registry.add_security_scheme("api_key", {
    "type": "apiKey",
    "in": "header",
    "name": "X-API-Key",
    "description": "API key for authentication"
})

@api_security("api_key")
async def api_key_route(req):
    ...
```

### OAuth2

```python
openapi_registry.add_security_scheme("oauth2", {
    "type": "oauth2",
    "flows": {
        "authorizationCode": {
            "authorizationUrl": "https://example.com/oauth/authorize",
            "tokenUrl": "https://example.com/oauth/token",
            "scopes": {
                "read": "Read access",
                "write": "Write access",
                "admin": "Admin access"
            }
        }
    }
})

@api_security("oauth2", scopes=["read", "write"])
async def oauth_route(req):
    ...
```

---

## 🎯 Best Practices

### 1. Always Define DTOs

```python
# Good ✅
@api_response(200, UserDto)

# Avoid ❌
@api_response(200, description="Returns user")
```

### 2. Use Descriptive Summaries

```python
# Good ✅
@api_operation(summary="Get user by ID")

# Avoid ❌
@api_operation(summary="Get user")
```

### 3. Document All Status Codes

```python
@api_response(200, UserDto, "Success")
@api_response(404, ErrorDto, "User not found")
@api_response(400, ErrorDto, "Invalid ID")
@api_response(500, ErrorDto, "Internal error")
```

### 4. Group with Tags

```python
@api_tags("Users", "Public")  # Multiple tags
```

### 5. Add Examples

```python
Field(
    description="User age",
    example=30,  # Single example
    examples=[25, 30, 35, 40]  # Multiple examples
)
```

### 6. Use Custom Validators

```python
class CreateUserDto(JswebBaseModel):
    email: str

    @validator('email')
    @classmethod
    def validate_email_domain(cls, value):
        if not value.endswith('@company.com'):
            raise ValueError('Must use company email')
        return value
```

---

## 📊 Comparison with Other Frameworks

### FastAPI

**FastAPI:**
```python
@app.post("/users")
async def create_user(user: CreateUserDto):
    return {"user": user.dict()}
```

**jsweb:**
```python
@api.route("/users", methods=["POST"])
@api_body(CreateUserDto)
async def create_user(req):
    return json({"user": req.validated_data})
```

### NestJS

**NestJS (TypeScript):**
```typescript
@Post('/users')
@ApiOperation({ summary: 'Create user' })
@ApiBody({ type: CreateUserDto })
async createUser(@Body() createUserDto: CreateUserDto) {
  return this.usersService.create(createUserDto);
}
```

**jsweb:**
```python
@api.route("/users", methods=["POST"])
@api_operation(summary="Create user")
@api_body(CreateUserDto)
async def create_user(req):
    return json({"user": req.validated_data})
```

---

## 🧪 Testing

### Testing DTOs

```python
from jsweb.dto import ValidationError

# Valid
user = UserDto(name="John", email="john@example.com", age=30)
assert user.name == "John"

# Invalid - raises ValidationError
try:
    user = UserDto(name="", email="invalid", age=-5)
except ValidationError as e:
    print(e.errors())
```

### Testing Routes with Validation

```python
import pytest
from jsweb.testing import TestClient

def test_create_user_valid():
    client = TestClient(app)
    response = client.post("/api/users", json={
        "name": "John",
        "email": "john@example.com",
        "age": 30
    })
    assert response.status_code == 201

def test_create_user_invalid():
    client = TestClient(app)
    response = client.post("/api/users", json={
        "name": "",
        "email": "invalid",
        "age": -5
    })
    assert response.status_code == 400
    assert "Validation failed" in response.json()["error"]
```

---

## 🚀 Deployment Checklist

### 1. Enable/Disable Docs Per Environment

```python
# config.py
import os

# Disable docs in production
ENABLE_OPENAPI_DOCS = os.getenv('ENVIRONMENT') != 'production'
```

### 2. Secure Your Docs

```python
# Only allow docs in dev/staging
if os.getenv('ENVIRONMENT') in ['development', 'staging']:
    ENABLE_OPENAPI_DOCS = True
else:
    ENABLE_OPENAPI_DOCS = False
```

### 3. Customize for Production

```python
# config.py
API_TITLE = "Production API"
API_DESCRIPTION = "Internal use only"
OPENAPI_DOCS_URL = "/internal/docs"  # Hide from public
```

---

## ❓ Troubleshooting

### Docs Not Showing

**Problem:** `/docs` returns 404

**Solutions:**
1. Check `ENABLE_OPENAPI_DOCS = True` in config.py
2. Make sure Pydantic is installed: `pip install pydantic>=2.0`
3. Verify routes are decorated with `@api_*` decorators

### Validation Not Working

**Problem:** Invalid requests still accepted

**Solutions:**
1. Make sure you're using `@api_body(MyDto)` decorator
2. Check `auto_validate=True` (default)
3. Verify Pydantic is installed

### Routes Not Appearing in Docs

**Problem:** Some routes missing from Swagger UI

**Solutions:**
1. Add `@api_operation()` decorator
2. Make sure blueprint is registered before `jsweb run`
3. Check logs for errors during introspection

---

## 📖 Additional Resources

- **OpenAPI Specification**: https://swagger.io/specification/
- **Swagger UI**: https://swagger.io/tools/swagger-ui/
- **ReDoc**: https://redocly.github.io/redoc/
- **Pydantic Documentation**: https://docs.pydantic.dev/

---

## ✨ Summary

### What You Get:

1. **Automatic Documentation** - Available at `/docs` on `jsweb run`
2. **Automatic Validation** - Request bodies validated with Pydantic
3. **Clean API** - Access via `req.validated_body` or `req.validated_data`
4. **NestJS-Style Control** - Fine-grained decorators when needed
5. **Zero Configuration** - Works out of the box
6. **Production Ready** - Battle-tested stack (Pydantic, OpenAPI 3.0)

### Quick Recap:

```python
# 1. Define DTO
class UserDto(JswebBaseModel):
    name: str = Field(max_length=100)
    email: str = Field(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')

# 2. Document Route
@api.route("/users", methods=["POST"])
@api_body(UserDto)  # Automatic validation!
@api_response(201, UserDto)
async def create_user(req):
    return json(req.validated_data)  # Already validated!

# 3. Run
# jsweb run

# 4. Visit /docs
```

**That's it! Your API is documented and validated automatically.** 🎉

---

*Last updated: 2025-12-10*
*jsweb version: 1.3.0+*
*Status: Production Ready*
