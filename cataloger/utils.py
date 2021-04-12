# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from flask import flash, Blueprint, request


def get_url_prefix(sub=""):
    return "/" + sub.lstrip("/").rstrip("/")


def flash_errors(form, category="warning"):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text} - {error}", category)
