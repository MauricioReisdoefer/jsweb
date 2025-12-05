# jsweb/admin.py
import os
import logging
from jsweb.blueprints import Blueprint
from jsweb.database import db_session
from jsweb.forms import Form, StringField
from jsweb.response import redirect, url_for, HTMLResponse
from jsweb.auth import admin_required, login_user
from sqlalchemy.inspection import inspect
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

class Admin:
    """
    The main class for the JsWeb Admin interface.
    """
    def __init__(self, app=None):
        self.models = {}
        self.blueprint = Blueprint("admin", url_prefix="/admin")
        
        template_path = os.path.join(os.path.dirname(__file__), "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_path))
        self.jinja_env.globals['url_for'] = url_for

        if app:
            self.init_app(app)

    def _render(self, template_name, **context):
        template = self.jinja_env.get_template(template_name)
        context['admin_models'] = self.models.keys()
        return HTMLResponse(template.render(**context))

    def init_app(self, app):
        self.app = app
        self._register_dashboard_and_login()
        self.app.register_blueprint(self.blueprint)

    def _register_dashboard_and_login(self):
        """Registers the main admin dashboard and handles login."""
        def index(request):
            error = None
            # If user is already an admin, show the dashboard
            if request.user and getattr(request.user, 'is_admin', False):
                # For now, just a welcome. We will add logs and tables later.
                return self._render("admin/dashboard.html", request=request)

            # Handle login form submission
            if request.method == "POST":
                from models import User  # Local import to avoid circular dependency
                username = request.form.get("username")
                password = request.form.get("password")
                
                user = User.query.filter_by(username=username).first()

                if user and user.is_admin and user.check_password(password):
                    response = redirect(url_for(request, 'admin.index'))
                    login_user(response, user)
                    return response
                else:
                    error = "Invalid credentials or not an admin."
            
            # Show the login page
            return self._render("admin/login.html", request=request, error=error)
        
        self.blueprint.add_route("/", index, endpoint="index", methods=["GET", "POST"])

    def _create_form_for_model(self, model, instance=None):
        form_fields = {}
        for column in inspect(model).c:
            if not column.primary_key:
                default_value = getattr(instance, column.name) if instance else ""
                form_fields[column.name] = StringField(
                    label=column.name.replace('_', ' ').title(),
                    default=str(default_value) if default_value is not None else ""
                )
        return type(f"{model.__name__}Form", (Form,), form_fields)

    def register(self, model):
        model_name = model.__name__
        self.models[model_name] = model
        pk_name = inspect(model).primary_key[0].name

        @admin_required
        def list_view(request):
            records = db_session.query(model).all()
            columns = [c.name for c in model.__table__.columns]
            records_data = [r.to_dict() for r in records]
            return self._render("admin/list.html", request=request, model_name=model_name, columns=columns, records=records_data, pk_name=pk_name)

        @admin_required
        def add_view(request):
            ModelForm = self._create_form_for_model(model)
            form = ModelForm(formdata=request.form)
            if request.method == "POST" and form.validate():
                new_record = model()
                for field_name, field in form._fields.items():
                    setattr(new_record, field_name, field.data)
                new_record.save()
                return redirect(url_for(request, f"admin.{model_name.lower()}_list"))
            return self._render("admin/form.html", request=request, model_name=model_name, form=form, record=None)

        @admin_required
        def edit_view(request, **kwargs):
            record_id = kwargs.get(pk_name)
            record = db_session.query(model).get(record_id)
            ModelForm = self._create_form_for_model(model, instance=record)
            form = ModelForm(formdata=request.form)
            if request.method == "POST" and form.validate():
                for field_name, field in form._fields.items():
                    setattr(record, field_name, field.data)
                record.save()
                return redirect(url_for(request, f"admin.{model_name.lower()}_list"))
            return self._render("admin/form.html", request=request, model_name=model_name, form=form, record=record)

        @admin_required
        def delete_view(request, **kwargs):
            record_id = kwargs.get(pk_name)
            record = db_session.query(model).get(record_id)
            record.delete()
            return redirect(url_for(request, f"admin.{model_name.lower()}_list"))

        self.blueprint.add_route(f"/{model_name.lower()}", list_view, endpoint=f"{model_name.lower()}_list")
        self.blueprint.add_route(f"/{model_name.lower()}/add", add_view, endpoint=f"{model_name.lower()}_add", methods=["GET", "POST"])
        self.blueprint.add_route(f"/{model_name.lower()}/edit/<int:{pk_name}>", edit_view, endpoint=f"{model_name.lower()}_edit", methods=["GET", "POST"])
        self.blueprint.add_route(f"/{model_name.lower()}/delete/<int:{pk_name}>", delete_view, endpoint=f"{model_name.lower()}_delete", methods=["POST"])
