# JsWeb 🚀

![License](https://img.shields.io/badge/license-MIT-blue.svg)
[![PyPI version](https://img.shields.io/pypi/v/jsweb)](https://pypi.org/project/jsweb/)

[![GitHub](https://img.shields.io/badge/GitHub-Jones--peter-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/Jones-peter)
[![Instagram](https://img.shields.io/badge/Instagram-jones__peter__-E4405F?style=flat-square&logo=instagram&logoColor=white)](https://www.instagram.com/jones_peter__/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Jones--Peter-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/jones-peter-121157221/)
[![Website](https://img.shields.io/badge/Website-jonespeter.site-0078D4?style=flat-square&logo=google-chrome&logoColor=white)](https://jonespeter.site)

A lightweight and modern Python web framework designed for speed, simplicity, and a great developer experience.

JsWeb provides the essential tools to build web applications and APIs quickly, without getting in your way. It's perfect for beginners learning web development and for experts who need to build and deploy fast.

---

## ✨ Features

-   **Simple Routing:** Expressive and easy-to-use decorator-based routing.
-   **Request & Response Objects:** Intuitive access to query parameters, form data, and response helpers.
-   **Jinja2 Templating:** Includes built-in support for the powerful Jinja2 templating engine.
-   **Custom Template Filters:** Easily extend Jinja2 with your own custom filters.
-   **Lightweight & Fast:** No unnecessary bloat. JsWeb is built to be quick and efficient.
-   **Built-in Dev Server:** A simple development server with auto-reload capabilities.
-   **Helpful CLI:** A command-line interface to create new projects and manage your application.
---
## 📦 Installation

Get started with JsWeb by installing it from PyPI using `pip`.

```bash
pip install jsweb
```
---
## 🚀 Getting Started: A Complete Example

This guide will walk you through creating a multi-feature web application in just a few minutes.

### 1. Create a New Project

Use the `jsweb` CLI to generate a new project structure.

```bash
jsweb new my_jsweb_app
cd my_jsweb_app
```

This creates a directory with a basic `app.py`, a `templates` folder, and a `static` folder.

### 2. Update Your `app.py`

Replace the contents of `my_jsweb_app/app.py` with the following code. This example demonstrates routing, forms, query parameters, and custom template filters.

```python
# my_jsweb_app/app.py

from jsweb import JsWebApp, run, render, __VERSION__, html

# Initialize the application
app = JsWebApp()


# Define a custom filter for use in Jinja2 templates
@app.filter("shout")
def shout(text):
    """Converts text to uppercase and adds exclamation marks."""
    return text.upper() + "!!!"


# Route for the home page
@app.route("/")
def home(req):
    """Renders a welcome page, passing context to the template."""
    # Example dictionary to pass to the template
    sample_data = {"one": "First Item", "two": "Second Item", "three": "Third Item"}
    
    # Get a query parameter from the URL (e.g., /?name=World)
    query_name = req.query.get("name", "Guest")
    
    # Data to be passed into the template
    context = {
        "name": query_name,
        "version": __VERSION__,
        "items": sample_data
    }
    return render("welcome.html", context)


# Route to display a simple HTML form
@app.route("/form")
def form(req):
    """Returns a raw HTML response with a form."""
    return html('''
    <h1>Submit Your Name</h1>
    <p><a href='/search?q=hello'>Test Query Params</a></p>
    <form method="POST" action="/submit">
        <input name="name" placeholder="Your name" />
        <button type="submit">Submit</button>
    </form>
    ''')


# Route to handle the form submission via POST
@app.route("/submit", methods=["POST"])
def submit(req):
    """Processes POST data from a form."""
    name = req.form.get("name", "Anonymous")
    return html(f"<h2>👋 Hello, {name}</h2>")


# Route to handle search queries from the URL
@app.route("/search")
def search(req):
    """Processes GET data from query parameters."""
    query = req.query.get("q", "")
    return html(f"<h2>🔍 You searched for: {query}</h2>")


# Standard entry point to run the app
if __name__ == "__main__":
    run(app)
```

### 3. Create the Template

Create a file named `welcome.html` inside the `templates` folder and add the following content. This template will use the data and custom filter we defined in `app.py`.

```html
<!-- my_jsweb_app/templates/welcome.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Welcome to JsWeb</title>
    <style>body { font-family: sans-serif; line-height: 1.6; padding: 2em; }</style>
</head>
<body>
    <h1>Hello, {{ name | shout }}</h1>
    <p>You are running JsWeb version <strong>{{ version }}</strong>.</p>
    
    <h3>Here is your data:</h3>
    <ul>
        {% for key, value in items.items() %}
            <li><strong>{{ key }}:</strong> {{ value }}</li>
        {% endfor %}
    </ul>
</body>
</html>
```

### 4. Run the Development Server

Now, run the application from your terminal:

```bash
jsweb run
```

The server will start on **http://127.0.0.1:8000**.

You can now test all the features:
-   **Home Page:** Open [http://127.0.0.1:8000](http://127.0.0.1:8000)
-   **With a Query Parameter:** Open [http://127.0.0.1:8000/?name=Alice](http://127.0.0.1:8000/?name=Alice)
-   **Form Page:** Open [http://127.0.0.1:8000/form](http://127.0.0.1:8000/form) to submit your name.
-   **Search Page:** Open [http://127.0.0.1:8000/search?q=python](http://127.0.0.1:8000/search?q=python)

## 📚 API Guide

### Application & Routing

Your application is an instance of `JsWebApp`. Routes are defined with the `@app.route()` decorator.

```python
from jsweb import JsWebApp

app = JsWebApp()

@app.route("/path")
def handler(req):
    # ...
    pass
```

By default, routes handle `GET` requests. To handle other methods, use the `methods` argument:

```python
@app.route("/submit", methods=["POST"])
def submit(req):
    # This function only runs for POST requests
    pass
```

### The Request Object (`req`)

Every route handler receives a `req` object, which gives you access to incoming request data.

-   `req.query`: A dictionary-like object for URL query parameters (the part after `?`).
    ```python
    # For a URL like /search?q=hello
    query = req.query.get("q", "")  # Returns "hello"
    ```
-   `req.form`: A dictionary-like object for data submitted from an HTML form via `POST`.
    ```python
    # For a form with <input name="name">
    name = req.form.get("name", "Anonymous")
    ```

### Creating Responses

You can return a response in several ways:

1.  **Render a Template:** Use the `render()` function to process a Jinja2 template. The second argument is a context dictionary, which makes variables available in the template.
    ```python
    from jsweb import render

    @app.route("/")
    def home(req):
        return render("template.html", {"name": "World"})
    ```

2.  **Return Raw HTML:** Use the `html()` helper to quickly return a string as an HTML response.
    ```python
    from jsweb import html

    @app.route("/simple")
    def simple(req):
        return html("<h1>This is a heading</h1>")
    ```

### Custom Template Filters

You can easily add your own Jinja2 filters with the `@app.filter()` decorator. The function name becomes the filter name.

```python
@app.filter("shout")
def shout(text):
    return text.upper() + "!!!"

# In a template: {{ my_variable | shout }}
```

## 💻 CLI Usage

-   `jsweb new <project_name>`
    -   Creates a new project directory with a starter template.
-   `jsweb run`
    -   Starts the development server in the current directory.
    -   `--host <ip>`: Sets the host to bind to (default: `127.0.0.1`).
    -   `--port <number>`: Sets the port to use (default: `8000`).
-   `jsweb --version`
    -   Displays the installed version of JsWeb.
- `jsweb run --host 0.0.0.0`  : for run server on your IP address on LAN

---
## Contributing 🤝💗
[![CONTRIBUTING](https://img.shields.io/badge/Contributing-Join%20Us-brightgreen)](CONTRIBUTING.md)


## Reporting Bugs 🪲

If you encounter a bug, please open an issue on GitHub. Please include the following:
* Your version of jsweb.
* A clear and concise description of the bug.
* Steps to reproduce the behavior.
* A code snippet demonstrating the issue.

## Suggesting Enhancements 💭📈

If you have an idea for a new feature, feel free to open an issue to discuss it. Please provide:
* A clear description of the feature and the problem it solves.
* Any sample code or use-cases you might have in mind.

## License 🔒

This project is licensed under the MIT License.

## Contact 📧

For any questions or support, please contact [jonespetersoftware@gmail.com].
