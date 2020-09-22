# -*- coding: utf-8 -*-
"""annotation views."""
import requests
import tempfile
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    flash,
    url_for,
    send_file,
    session,
)
from flask_login import login_required, current_user

from .forms import (
    NewAnnotationForm,
    SearchAnnotationForm,
    NewCardForm,
    EditCardForm,
)

from .models import Card, Organism, Process, Sample, Marker, Gene, Method

# TODO store this as a secret, duh
API_KEY = "3d441415-6164-487b-8ec3-1be7d9fd7383"

classes = {
    "organisms": Organism,
    "processes": Process,
    "samples": Sample,
    "markers": Marker,
    "genes": Gene,
    "methods": Method,
}


blueprint = Blueprint(
    "cards",
    __name__,
    url_prefix="/cards",
    static_folder="../static",
)

ontologies = {
    "organisms": ("NCBITAXON",),
    "samples": ("GO", "MESH", "CLO", "FB-BT", "NCIT"),
    "processes": ("GO", "MESH", "NCIT"),
    "methods": ("FBbi", "EDAM-BIOIMAGING", "BAO"),
    "genes": ("GO",),
    "markers": None,  # ("FBbi", "EDAM-BIOIMAGING"),
}


def search_bioportal(search_text, **other_params):
    """Searches the bioontology database for the term search_text"""

    params = {
        "apikey": API_KEY,
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

    suggestions = search_bioportal(search_term, ontologies=ontologies[cls])

    if not suggestions:
        flash("No results found, please reformulate your query :)", "warning")
        form = SearchAnnotationForm()
        form.search_term.data = search_term
        return render_template("annotations/search_annotation.html", form=form, cls=cls)

    new_annotation_form = NewAnnotationForm()
    new_annotation_form.select_term.choices = [
        (term_id, _format_label(term)) for term_id, term in suggestions.items()
    ]

    if request.method == "POST":
        term_id = new_annotation_form.select_term.data
        term = suggestions[term_id]
        if cls in ("organisms", "methods"):
            new = classes[cls](label=term["prefLabel"], bioportal_id=term["@id"])
        else:
            new = classes[cls](
                label=term["prefLabel"], bioportal_id=term["@id"], organism_id=0
            )
        new.save()
        flash(f"Saved new term {new.label}", "success")
        return redirect(url_for("cards.new_card"))

    return render_template(
        "annotations/new_annotation.html", form=new_annotation_form, cls=cls
    )


def _format_label(term):
    label = term["prefLabel"]
    ontology_id = term["links"]["ontology"]
    try:
        ontology = requests.get(ontology_id, params={"apikey": API_KEY}).json()[
            "acronym"
        ]
    except Exception:
        ontology = ""
    definition = term.get("definition")

    if definition:
        split = definition[0].split()
        if len(split) > 20:
            short = " ".join(split[:20]) + "..."
        else:
            short = definition
        return f"{label}: {short} \t ({ontology})"
    else:
        return f"{label} \t ({ontology})"


@blueprint.route("/")
@login_required
def cards():
    """List all cards"""
    cards = Card.query.all()
    return render_template("annotations/cards.html", cards=cards)


@blueprint.route(
    "/new-card/",
    methods=["GET", "POST"],
)
@login_required
def new_card():
    """Creates a card"""
    form = NewCardForm()
    if form.add_marker.data:
        form.select_markers.append_entry()
        return render_template("annotations/new_card.html", form=form)
    if form.remove_marker.data and len(form.select_markers):
        form.select_markers.pop_entry()
        return render_template("annotations/new_card.html", form=form)

    if form.add_gene.data:
        form.select_genes.append_entry()
        return render_template("annotations/new_card.html", form=form)
    if form.remove_gene.data and len(form.select_genes):
        form.select_genes.pop_entry()
        return render_template("annotations/new_card.html", form=form)

    # if form.validate_on_submit():
    if request.method == "POST":
        card = Card(
            title=form.title.data,
            user_id=current_user.id,
            organism_id=form.select_organism.data,
            process_id=form.select_process.data,
            sample_id=form.select_sample.data,
            comment=form.comment.data,
            markers=[
                Marker.get_by_id(m.select_marker.data)
                for m in form.select_markers.entries
            ],
            genes=[
                Gene.get_by_id(m.select_gene.data) for m in form.select_genes.entries
            ],
        )
        flash(f"New card {card.title} created by user {current_user.id}", "success")
        card.save()
        return redirect("/users")
    return render_template("annotations/new_card.html", form=form)


@blueprint.route(
    "/delete/<card_id>",
    methods=["GET"],
)
@login_required
def delete_card(card_id):
    card = Card.query.filter_by(id=card_id).first()
    card.delete()
    return redirect("/users")


@blueprint.route(
    "/edit/<card_id>",
    methods=["GET", "POST"],
)
@login_required
def edit_card(card_id):
    card = Card.query.filter_by(id=card_id).first()
    form = EditCardForm(card_id=card_id)

    if form.add_marker.data:
        form.select_markers.append_entry()
        return render_template("annotations/new_card.html", form=form)
    if form.remove_marker.data and len(form.select_markers):
        form.select_markers.pop_entry()
        return render_template("annotations/new_card.html", form=form)

    if form.add_gene.data:
        form.select_genes.append_entry()
        return render_template("annotations/new_card.html", form=form)
    if form.remove_gene.data and len(form.select_genes):
        form.select_genes.pop_entry()
        return render_template("annotations/new_card.html", form=form)

    # if form.validate_on_submit():
    if request.method == "POST":
        card.update(
            title=form.title.data,
            user_id=current_user.id,
            organism_id=form.select_organism.data,
            process_id=form.select_process.data,
            sample_id=form.select_sample.data,
            method_id=form.select_method.data,
            comment=form.comment.data,
            markers=[
                Marker.get_by_id(m.select_marker.data)
                for m in form.select_markers.entries
            ],
            genes=[
                Gene.get_by_id(m.select_gene.data) for m in form.select_genes.entries
            ],
        )
        card.save()
        flash(f"Edited {card.title} by user {current_user.id}", "success")
        return redirect("/users")

    # executed only with a GET
    form.title.data = card.title
    form.select_organism.data = card.organism_id
    form.select_process.data = card.process_id
    form.select_sample.data = card.sample_id
    form.comment.data = card.comment

    while len(form.select_markers):
        form.select_markers.pop_entry()
    while len(form.select_genes):
        form.select_genes.pop_entry()

    for marker in card.markers:
        mrk = form.select_markers.append_entry()
        mrk.select_marker.data = marker.id
    for gene in card.genes:
        gne = form.select_genes.append_entry()
        gne.select_gene.data = gene.id

    return render_template("annotations/new_card.html", form=form)


@blueprint.route(
    "/download/<card_id>",
    methods=["GET"],
)
@login_required
def download_card(card_id):
    card = Card.query.filter_by(id=card_id).first()
    _, tmp_yml = tempfile.mkstemp(suffix=".yml")
    with open(tmp_yml, "w") as fh:
        fh.write("# omero annotation file")
        fh.write(card.as_yml())
        fh.seek(0)
    return send_file(
        tmp_yml, as_attachment=True, attachment_filename="omero_annotation.yml"
    )
