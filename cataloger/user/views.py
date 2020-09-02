# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ..annotations.models import Card

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")


@blueprint.route("/")
@login_required
def cards():
    """List cards"""

    user_id = current_user.id
    cards = Card.query.filter_by(user_id=user_id)
    return render_template("annotations/cards.html", cards=cards)
