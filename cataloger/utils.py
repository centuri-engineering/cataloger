# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, Blueprint


def flash_errors(form, category="warning"):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text} - {error}", category)


class CataBlueprint(Blueprint):
    """Subclass blueprint to route to subdirectory
    'cataloger'
    """

    def route(self, path, *args, **kwargs):
        if "url_prefix" in kwargs:
            url_prefix = kwargs.pop("url_prefix")

        else:
            url_prefix = ""

        return super().route("/cataloger" + url_prefix + path, *args, **kwargs)
