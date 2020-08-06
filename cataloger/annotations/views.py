# -*- coding: utf-8 -*-
"""annotation views."""
import requests
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required

from .forms import NewAnnotationForm, SearchAnnotationForm, NewCardForm
from .models import Card, Organism, Process, Sample, Marker, Gene, Method


classes = {
    "organisms": Organism,
    "processes": Process,
    "samples": Sample,
    "markers": Marker,
    "genes": Gene,
    "methods": Method,
}


blueprint = Blueprint(
    "cards", __name__, url_prefix="/cards", static_folder="../static",
)


def search_bioportal(search_text, **other_params):
    """Searches the bioontology database for the term search_text
    """

    params = {
        # TODO store this as a secret, duh
        "apikey": "3d441415-6164-487b-8ec3-1be7d9fd7383",
        "q": search_text,
        "suggest": True,
    }
    params.update(other_params)
    response = requests.get(f"http://data.bioontology.org/search", params=params).json()

    return {term["@id"]: term for term in response["collection"]}


@blueprint.route("/search/", methods=["GET", "POST"], defaults={"cls": "organisms"})
@blueprint.route("/search/<cls>", methods=["GET", "POST"])
@login_required
def search_annotation(cls):
    """Search an annotation in Bioportal."""
    form = SearchAnnotationForm()
    if request.method == "POST":
        search_term = form.search_term.data
        return redirect(url_for(".new_annotation", cls=cls, search_term=search_term))

    return render_template("annotations/search_annotation.html", form=form, cls=cls)


@blueprint.route(
    "/new-term/",
    methods=["GET", "POST"],
    defaults={"cls": "organisms", "search_term": "pombe"},
)
@blueprint.route("/new-term/<cls>", methods=["GET", "POST"])
@login_required
def new_annotation(cls, search_term=None):
    """New annotation."""
    if search_term is None:
        search_term = request.args.get("search_term")

    suggestions = search_bioportal(search_term)

    if not suggestions:
        flash("No results found, maybe reformulate?")
        return redirect("/")

    new_annotation_form = NewAnnotationForm()
    new_annotation_form.select_term.choices = [
        (term_id, _format_label(term)) for term_id, term in suggestions.items()
    ]

    if request.method == "POST":
        term_id = new_annotation_form.select_term.data
        term = suggestions[term_id]
        new = classes[cls](label=term["prefLabel"], bioportal_id=term["@id"])
        new.save()
        flash(f"Saved new term {new}")
        return redirect("/")

    return render_template(
        "annotations/new_annotation.html", form=new_annotation_form, cls=cls
    )


def _format_label(term):
    label = term["prefLabel"]

    definition = term.get("definition")
    if definition:
        split = definition[0].split()
        if len(split) > 30:
            short = " ".join(split[:30]) + "..."
        else:
            short = definition
        return f"{label}: {short}"
    else:
        return label


@blueprint.route(
    "/new-card/", methods=["GET", "POST"],
)
@login_required
def new_card():

    form = NewCardForm()
    if request.method == "POST":
        card = Card(
            title=form.title.data,
            organism_id=form.select_organism.data,
            process_id=form.select_process.data,
            sample_id=form.select_sample.data,
        )
        flash(f"New card {card}")
        return redirect("/")

    return render_template("annotations/new_card.html", form=form)
