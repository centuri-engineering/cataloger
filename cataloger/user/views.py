# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template
from flask_login import login_required

from ..annotations.models import Card

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")


@blueprint.route("/")
@login_required
def cards():
    """List cards"""
    cards = Card.query.all()

    return render_template("users/cards.html", cards=cards)
