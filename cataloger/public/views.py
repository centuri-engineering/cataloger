# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
import logging

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

from cataloger.extensions import login_manager, ldap_manager, omero_manager
from cataloger.public.forms import LoginForm
from cataloger.user.forms import RegisterForm, NewGroupForm
from cataloger.user.models import User, Group
from cataloger.utils import flash_errors, get_url_prefix


blueprint = Blueprint(
    "public", __name__, url_prefix=get_url_prefix(), static_folder="../static"
)

log = logging.getLogger(__name__)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))


@omero_manager.save_user
def save_user_omero(user_info):

    username = user_info["username"]

    existing = User.query.filter_by(username=username).first()
    if existing:
        log.warning("User %s is already registered", username)
        return existing

    name = user_info.get("fullname", "").split()
    first = last = None
    if len(name) > 1:
        first = name[0]
        last = " ".join(name[1:])
    elif len(name) == 1:
        last = username

    groupname = user_info.get("groupname", "default")
    groups = Group.query.filter_by(groupname=groupname)
    if groups.first():
        group = groups.first()
        current_app.logger.info("Found group %s", groupname)
    else:
        group = Group.create(
            groupname=groupname,
            active=True,
        )
        current_app.logger.info("Created group %s", groupname)

    user = User.create(
        username=username,
        first_name=first,
        last_name=last,
        active=True,
        group_id=group.id,
    )

    return user


@ldap_manager.save_user
def save_user_ldap(dn, username, user_info, memberships):
    """Saves a user that managed to log in with LDAP

    Group determination method is based on the first 'OU=' section
    in the user DN, might need tweaking
    """
    existing = User.query.filter_by(username=username).first()
    if existing:
        log.warning("User %s is already registered", username)
        return existing

    name = user_info.get("cn", "").split()

    first = last = None
    if len(name) > 1:
        first = name[0]
        last = " ".join(name[1:])
    elif len(name) == 1:
        last = username

    groupname = None
    for sec in dn.split(","):
        if sec.startswith("OU"):
            groupname = sec.split("=")[1]
            break
    else:
        groupname = "default"

    groups = Group.query.filter_by(groupname=groupname)
    if groups.first():
        group = groups.first()
        current_app.logger.info("Found group %s", groupname)
    else:
        group = Group.create(
            groupname=groupname,
            active=True,
        )
        current_app.logger.info("Created group %s", groupname)

    user = User.create(
        username=username,
        first_name=first,
        last_name=last,
        active=True,
        group_id=group.id,
    )

    return user


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
        login_user(form.user)
        flash("Thank you for registering. You are now logged in.", "success")
        return redirect(url_for("user.cards"))
    else:
        flash_errors(form)
    return render_template("public/register.html", form=form)


@blueprint.route("/new-group/", methods=["GET", "POST"])
@login_required
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
