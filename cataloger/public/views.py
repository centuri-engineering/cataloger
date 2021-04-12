# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required, login_user, logout_user

from cataloger.extensions import login_manager
from cataloger.public.forms import LoginForm
from cataloger.user.forms import RegisterForm, NewGroupForm
from cataloger.user.models import User, Group
from cataloger.utils import flash_errors, get_url_prefix


blueprint = Blueprint(
    "public", __name__, url_prefix=get_url_prefix(), static_folder="../static"
)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))


@blueprint.route("/", methods=["GET", "POST"])
def home():
    """Home page."""
    form = LoginForm(request.form)
    current_app.logger.info("Hello from the home page!")
    # Handle logging in
    current_app.logger.info("request root: %s", request.script_root)
    current_app.logger.info("request path: %s", request.path)
    current_app.logger.info("request method: %s", request.method)

    if request.method == "POST":
        if form.validate_on_submit():
            login_user(form.user)
            flash("You are logged in.", "success")
            return redirect(url_for("user.cards"))
        else:
            flash_errors(form)
            return redirect(url_for("user.cards"))

    return render_template("public/home.html", form=form)


@blueprint.route("/quick_start", methods=["GET", "POST"])
def quick_start():
    """Quick start page."""
    return render_template("public/quick_start.html")


@blueprint.route("/logout/")
@login_required
def logout():
    """Logout."""
    logout_user()
    flash("You are logged out.", "info")
    return redirect(url_for("public.home"))


@blueprint.route("/register/", methods=["GET", "POST"])
def register():
    """Register new user."""
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            active=True,
        )
        flash("Thank you for registering. You can now log in.", "success")
        return redirect(url_for("public.home"))
    else:
        flash_errors(form)
    return render_template("public/register.html", form=form)

@blueprint.route("/new-group/", methods=["GET", "POST"])
def create_group():
    """Register new group."""
    grp_form = NewGroupForm(request.form)
    if grp_form.validate_on_submit():
        Group.create(
            groupname=grp_form.groupname.data,
            active=True,
        )
        flash("New group created.", "success")
        return redirect(url_for("public.home"))
    else:
        flash_errors(grp_form)
    return render_template("public/newgroup.html", grp_form=grp_form)

@blueprint.route("/about/")
def about():
    """About page."""
    form = LoginForm(request.form)
    return render_template("public/about.html", form=form)
