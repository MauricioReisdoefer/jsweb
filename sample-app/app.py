# D:/jones/Python/jsweb/sample-app/app.py

from jsweb import JsWebApp, run, render, html, json, __VERSION__
import config
import models
# ✅ 1. Import the User model
from models import User
# Initialize the database connection when running the app
from jsweb.database import DatabaseError

app = JsWebApp(static_url=config.STATIC_URL, static_dir=config.STATIC_DIR, template_dir=config.TEMPLATE_FOLDER,
               db_url=config.DATABASE_URL)


@app.route("/")
def home(req):
    return render("welcome.html", {"name": config.APP_NAME, "version": config.VERSION, "library_version": __VERSION__})


# ✅ 2. Add a new route to create a user
@app.route("/add-user")
def add_user(req):
    """Creates a new user and saves it to the database."""
    try:
        name = req.query.get("name")
        email = req.query.get("email")

        new_user = User(
            name=name,
            email=email
        )
        new_user.save()
        return json(new_user.to_dict(), status=201)
    except DatabaseError as e:
        # Catch the specific, clean error from the database layer
        error_response = {
            "error": "Could not create user.",
            "detail": str(e)
        }
        # Return a 409 Conflict status, which is more appropriate for duplicates
        return json(error_response, status=409)
    except Exception as e:
        # Fallback for other unexpected errors
        return json({"error": "An unexpected error occurred.", "detail": str(e)}, status=500)


@app.route("/users/search")
def search_users(req):
    # Get the search term from a query parameter, e.g., /users/search?q=john
    search_term = req.query.get("q", "")

    try:
        query = User.query().filter(User.name.ilike(f"%{search_term}%"))
        users = query.order_by(User.name).all()
        user_list = [user.to_dict() for user in users]
        return json(user_list)

    except DatabaseError as e:
        return json({"error": "A database error occurred.", "detail": str(e)}, status=500)


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


if __name__ == "__main__":
    run(app, host=config.HOST, port=config.PORT)
