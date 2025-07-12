# jsweb/cli.py
import argparse
import logging
import os
import socket
import sys

from alembic import command
from alembic.autogenerate import produce_migrations
from alembic.config import Config
from alembic.operations.ops import AddColumnOp, DropColumnOp, AlterColumnOp, CreateTableOp, DropTableOp
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

from jsweb import __VERSION__
from jsweb.server import run

JSWEB_DIR = os.path.dirname(__file__)
TEMPLATE_FILE = os.path.join(JSWEB_DIR, "templates", "starter_template.html")
STATIC_FILE = os.path.join(JSWEB_DIR, "static", "global.css")


def create_project(name):
    """Creates a new project scaffold."""
    os.makedirs(name, exist_ok=True)
    os.makedirs(os.path.join(name, "templates"), exist_ok=True)
    os.makedirs(os.path.join(name, "static"), exist_ok=True)
    # The migration system needs a home
    os.makedirs(os.path.join(name, "migrations"), exist_ok=True)

    # Copy template and CSS
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        starter_html = f.read()
    with open(os.path.join(name, "templates", "welcome.html"), "w", encoding="utf-8") as f:
        f.write(starter_html)
    with open(STATIC_FILE, "r", encoding="utf-8") as f:
        css = f.read()
    with open(os.path.join(name, "static", "global.css"), "w", encoding="utf-8") as f:
        f.write(css)

    # Create a more complete models.py
    with open(os.path.join(name, "models.py"), "w", encoding="utf-8") as f:
        f.write("""
from jsweb.database import ModelBase, String, Integer, Column

# Example Model
class User(ModelBase):
    __tablename__ = 'users' # Explicit table name is good practice
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, nullable=False)
""")
    # Create a config.py file
    with open(os.path.join(name, "config.py"), "w", encoding="utf-8") as f:
        f.write(f"""
# config.py
import os

APP_NAME = "{name.capitalize()}"
DEBUG = True
VERSION = "0.1.0"

# Use an absolute path for SQLite to avoid ambiguity
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# ✅ FIX: Escaped the inner f-string's curly braces with {{ and }}
DATABASE_URL = f"sqlite:///{{os.path.join(BASE_DIR, 'jsweb.db')}}"
# DATABASE_URL = "postgresql://user:pass@host:port/dbname"

HOST = "127.0.0.1"
PORT = 8000
""")
    # Create an app.py that does NOT manage the database
    with open(os.path.join(name, "app.py"), "w", encoding="utf-8") as f:
        f.write(f"""
from jsweb import JsWebApp, run, __VERSION__, render
import config
import models

app = JsWebApp(static_url=config.STATIC_URL, static_dir=config.STATIC_DIR, template_dir=config.TEMPLATE_FOLDER)

@app.route("/")
def home(req):
    return render("welcome.html", {{"name": config.APP_NAME, "version":config.VERSION, "library_version": __VERSION__}})

if __name__ == "__main__":
    # Initialize the database connection when running the app
    from jsweb.database import init_db
    init_db(config.DATABASE_URL)
    run(app, host=config.HOST, port=config.PORT)
""")

    print(f"✔️ Project '{name}' created successfully in '{os.path.abspath(name)}'.")
    print(
        f"👉 To get started, run:\n  cd {name}\n  jsweb db makemigrations -m \"Initial migration\"\n  jsweb db migrate\n  jsweb run")


# --- Helper functions (check_port, get_local_ip, display_qr_code) remain the same ---
def check_port(host, port):
    """Checks if a port is available on the given host."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
        return True
    except OSError:
        return False


def get_local_ip():
    """Tries to determine the local IP address of the machine for LAN access."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def display_qr_code(url):
    """Generates and prints a QR code for the given URL to the terminal."""
    import qrcode
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make(fit=True)
    print("📱 Scan the QR code to access the server on your local network:")
    qr.print_tty()
    print("-" * 40)


def patch_env_py():
    path = os.path.join("migrations", "env.py")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Patch metadata for autogenerate
    if "target_metadata = None" in content:
        content = content.replace(
            "target_metadata = None",
            "from models import *\nfrom jsweb.database import ModelBase\n\ntarget_metadata = ModelBase.metadata"
        )

    # Patch render_as_batch for SQLite
    if "context.configure(" in content and "render_as_batch=True" not in content:
        content = content.replace(
            "context.configure(",
            "context.configure(\n        render_as_batch=True,"
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Patched env.py for metadata and batch mode.")


def setup_alembic_if_needed():
    if not os.path.exists("migrations"):
        print("⚙️  Initializing Alembic...")
        os.system("alembic init migrations")

        # Move and patch config
        if os.path.exists("alembic.ini"):
            os.rename("alembic.ini", "migrations/config.ini")

        with open("migrations/config.ini", "r+", encoding="utf-8") as f:
            content = f.read()
            content = content.replace("script_location = .", "script_location = migrations")
            f.seek(0)
            f.write(content)
            f.truncate()

        patch_env_py()
        print("✅ Patched env.py for metadata and batch mode.")
    else:
        pass


def get_alembic_config(db_url):
    cfg = Config("migrations/config.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)
    cfg.set_main_option("script_location", "migrations")  # important!
    return cfg


def is_db_up_to_date(config):
    engine = create_engine(config.get_main_option("sqlalchemy.url"))
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()
        script = ScriptDirectory.from_config(config)
        head_rev = script.get_current_head()
        return current_rev == head_rev


def has_model_changes(database_url, metadata):
    from sqlalchemy import create_engine
    from alembic.runtime.migration import MigrationContext
    from alembic.autogenerate import compare_metadata

    engine = create_engine(database_url)
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        diffs = compare_metadata(context, metadata)
    return bool(diffs)


def preview_model_changes_readable(database_url, metadata):
    engine = create_engine(database_url)
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        migration_script = produce_migrations(context, metadata)

        changes = []

        for op in migration_script.upgrade_ops.ops:
            if isinstance(op, AddColumnOp):
                changes.append(f"🆕 Added column '{op.column.name}' to table '{op.table_name}'")
            elif isinstance(op, DropColumnOp):
                changes.append(f"❌ Dropped column '{op.column_name}' from table '{op.table_name}'")
            elif isinstance(op, AlterColumnOp):
                change_desc = f"✏️ Altered column '{op.column_name}' in table '{op.table_name}'"
                if op.modify_nullable is not None:
                    change_desc += f" (nullable = {op.modify_nullable})"
                if op.modify_type is not None:
                    change_desc += f" (changed type)"
                changes.append(change_desc)
            elif isinstance(op, CreateTableOp):
                changes.append(f"🆕 Created table '{op.table_name}' with {len(op.columns)} columns")
            elif isinstance(op, DropTableOp):
                changes.append(f"❌ Dropped table '{op.table_name}'")
            else:
                changes.append(f"⚠️  Unhandled change: {op.__class__.__name__}")

        return changes if changes else None


def disable_logging_in_config():
    config_path = os.path.join("migrations", "config.ini")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Remove [loggers], [handlers], [formatters] and their keys
        filtered_lines = []
        skip = False
        for line in lines:
            if line.strip().startswith("[loggers]") or \
               line.strip().startswith("[handlers]") or \
               line.strip().startswith("[formatters]"):
                skip = True
                continue
            if skip and line.strip().startswith("[") and "]" in line:
                skip = False  # end section
            if not skip:
                filtered_lines.append(line)

        with open(config_path, "w", encoding="utf-8") as f:
            f.writelines(filtered_lines)

def cli():
    parser = argparse.ArgumentParser(prog="jsweb", description="JsWeb CLI - A lightweight Python web framework.")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__VERSION__}")
    sub = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # --- Run Command ---
    run_cmd = sub.add_parser("run", help="Run the JsWeb application in the current directory.")
    run_cmd.add_argument("--host", default="127.0.0.1", help="Host address to bind to (default: 127.0.0.1)")
    run_cmd.add_argument("--port", type=int, default=8000, help="Port number to listen on (default: 8000)")
    run_cmd.add_argument("--qr", action="store_true", help="Display a QR code for the server's LAN address.")

    # --- New Command ---
    new_cmd = sub.add_parser("new", help="Create a new JsWeb project.")
    new_cmd.add_argument("name", help="The name of the new project")

    db_cmd = sub.add_parser("db", help="Database migration tools")
    db_sub = db_cmd.add_subparsers(dest="subcommand", help="Migration actions", required=True)

    makemigrations_cmd = db_sub.add_parser(
        "makemigrations",
        help="Detect model changes and create a migration file."
    )
    makemigrations_cmd.add_argument("-m", "--message", required=True,
                                    help="A short, descriptive message for the migration.")

    db_sub.add_parser("migrate", help="Apply all pending migrations to the database.")

    args = parser.parse_args()
    sys.path.insert(0, os.getcwd())
    if args.command == "run":
        if args.qr:
            try:
                import qrcode
            except ImportError:
                print("❌ Error: The 'qrcode' library is required for the --qr feature.")
                print("   Please install it by running: pip install \"jsweb[qr]\"")
                return  # Exit gracefully

        if not os.path.exists("app.py"):
            print("❌ Error: Could not find 'app.py'. Ensure you are in a JsWeb project directory.")
            return
        if not check_port(args.host, args.port):
            print(f"❌ Error: Port {args.port} is already in use. Please specify a different port using --port.")
            return
        if args.qr:
            # For QR code, we need a specific LAN IP, not 0.0.0.0 or 127.0.0.1
            lan_ip = get_local_ip()
            url = f"http://{lan_ip}:{args.port}"
            display_qr_code(url)
        try:
            import importlib.util
            import config
            from jsweb.database import init_db, DatabaseError
            init_db(config.DATABASE_URL)
            spec = importlib.util.spec_from_file_location("app", "app.py")
            if spec is None or spec.loader is None:
                raise ImportError("Could not load app.py")
            sys.path.insert(0, os.getcwd())

            app_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(app_module)

            if not hasattr(app_module, "app"):
                raise AttributeError("Application instance 'app' not found in app.py")
            run(app_module.app, host=args.host, port=args.port)

        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user.")
        except ImportError as e:
            print(f"❌ Error: Could not import application.  Check your app.py file. Details: {e}")
        except AttributeError as e:
            print(
                f"❌ Error: Invalid application file. Ensure 'app.py' defines a JsWebApp instance named 'app'. Details: {e}")
        except Exception as e:
            print(f"❌ Error: Failed to run app.  Details: {e}")

    elif args.command == "new":
        create_project(args.name)
    elif args.command == "db":
        try:
            import config
            import models  # should contain ModelBase
            from jsweb.database import init_db
            init_db(config.DATABASE_URL)
        except Exception as e:
            print(f"❌ Error importing config/models: {e}")
            return

        setup_alembic_if_needed()
        alembic_cfg = get_alembic_config(config.DATABASE_URL)

        if args.subcommand == "makemigrations":
            if not is_db_up_to_date(alembic_cfg):
                print("❌ Cannot make new migration: Your database is not up to date.")
                print("👉 Run `jsweb db migrate` first to apply existing migrations.")
                return
            if not has_model_changes(config.DATABASE_URL, models.ModelBase.metadata):
                print("❌ Cannot make new migration: No changes in models")
                return
            changes = preview_model_changes_readable(config.DATABASE_URL, models.ModelBase.metadata)
            if not changes:
                print("❌ Cannot make new migration: No changes in models")
                return

            print("📋 The following changes will be applied:")
            print("=" * 40)
            for change in changes:
                print(change)
            print("=" * 40)
            confirm = input("✅ Create this migration? [y/N]: ").strip().lower()
            if confirm != "y":
                print("❌ Migration aborted.")
                return
            command.revision(alembic_cfg, autogenerate=True, message=args.message)
            print("✅ Migration created.")
        elif args.subcommand == "migrate":
            command.upgrade(alembic_cfg, "head")

    else:
        parser.print_help()
