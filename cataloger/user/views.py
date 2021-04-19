# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template, request, flash, url_for, redirect
from flask_login import login_required, current_user

from cataloger.annotations.models import Card
from cataloger.utils import flash_errors, get_url_prefix
from cataloger.user.models import User, Group
from cataloger.user.forms import EditUserForm, CreateUserForm

blueprint = Blueprint(
    "user", __name__, url_prefix=get_url_prefix("users"), static_folder="../static"
)


@blueprint.route("/")
@login_required
def cards():
    """List cards"""

    user_id = current_user.id
    cards = Card.query.filter_by(user_id=user_id)
    return render_template("annotations/cards.html", cards=cards)


@blueprint.route("/edit_user/<username>", methods=["GET", "POST"])
@login_required
def edit_user(username):
    """Edit user settings"""
    form = EditUserForm(request.form)
    if username == "me":
        form.user = current_user
        form.user.password = None
    elif current_user.id == 1:  # cheap is_admin test, FIXME
        form.user = User.query.filter_by(username=username).first()
        if not form.user:
            flash(f"Unknown user {username}", "warning")
            return redirect(url_for("user.cards"))
    form.username.data = form.user.username
    if not form.user.password:
        form.old_password.validators = []
        form.password.validators = []
        form.confirm.validators = []

    if form.validate_on_submit():
        flash(f"User {username} info updated", "success")
        form.user.update(
            first_name=form.firstname.data,
            last_name=form.lastname.data,
            group_id=form.select_group.data,
        )
        if form.user.password:
            form.user.set_password(form.password.data)

        return redirect(url_for("user.cards"))

    flash_errors(form)

    form.firstname.data = form.user.first_name
    form.lastname.data = form.user.last_name
    form.select_group.choices = [(form.user.group_id, form.user.group.groupname)] + [
        (g.id, g.groupname) for g in Group.query.all()
    ]

    return render_template("users/edit_user.html", form=form)


@blueprint.route("/create_user/<username>", methods=["GET", "POST"])
@login_required
def create_user(username):
    """Edit user settings"""
    form = CreateUserForm(request.form)
    form.username.data = username
    # cheap is_admin test, FIXME
    if current_user.id != 1 and not current_user.is_admin:

        flash(f"You are not authorized to access this page", "warning")
        return redirect(url_for("user.cards"))

    if form.validate_on_submit():
        flash(f"User {username} created", "success")
        return redirect(url_for("user.cards"))
    else:
        flash_errors(form)

    return render_template("users/create_user.html", form=form)
