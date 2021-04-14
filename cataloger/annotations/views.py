# -*- coding: utf-8 -*-
"""annotation views."""
import os
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

from cataloger.annotations.forms import (
    NewAnnotationForm,
    SearchAnnotationForm,
    NewCardForm,
    EditCardForm,
    NewProjectForm,
)

from cataloger.annotations.models import (
    Card,
    Organism,
    Process,
    Sample,
    Marker,
    Gene,
    Method,
    Project,
)

from cataloger.utils import get_url_prefix


# https://bioportal.bioontology.org/help#Getting_an_API_key

BIOPORTAL_API_KEY = os.environ.get("BIOPORTAL_API_KEY")
if not BIOPORTAL_API_KEY:
    raise ValueError(
        """
To use this service, you need an API key provided
by bioportal here: https://bioportal.bioontology.org/help#Getting_an_API_key,
this key should then be stored as the environement variable BIOPORTAL_API_KEY
"""
    )


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
    url_prefix=get_url_prefix("cards"),
    static_folder="../static",
)

ontologies = {
    "organisms": ("NCBITAXON",),
    "samples": ("FB-BT", "GO", "MESH", "CLO", "NCIT"),
    "processes": ("GO", "MESH", "NCIT"),
    "methods": ("FBbi", "EDAM-BIOIMAGING", "BAO"),
    "genes": ("GO",),
    "markers": None,  # ("FBbi", "EDAM-BIOIMAGING"),
}


def search_bioportal(search_text, **other_params):
    """Searches the bioontology database for the term search_text"""

    params = {
        "apikey": BIOPORTAL_API_KEY,
        "q": search_text,
        "suggest": False,
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

    suggestions = search_bioportal(search_term)  # , ontologies=ontologies[cls])

    if not suggestions:
        flash(
            """ No results found, please reformulate your quey, with more general
(and correctly spelled) terms""",
            "warning",
        )
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
        match = classes[cls].query.filter_by(label=term["prefLabel"]).first()
        if match:
            flash(f"The term {term['prefLabel']} is already registered", "warning")
            form = SearchAnnotationForm()
            return redirect(url_for(".search_annotation", form=form, cls=cls))

        if cls in ("organisms", "methods"):
            new = classes[cls](label=term["prefLabel"], bioportal_id=term["@id"])
        else:
            # TODO track organism
            new = classes[cls](
                label=term["prefLabel"], bioportal_id=term["@id"], organism_id=0
            )
        new.save()
        flash(f"Saved new term {new.label}", "success")
        form = SearchAnnotationForm()
        return redirect(url_for(".search_annotation", form=form, cls=cls))
    return render_template(
        "annotations/new_annotation.html", form=new_annotation_form, cls=cls
    )


def _format_label(term):
    label = term["prefLabel"]
    ontology_id = term["links"]["ontology"]

    # try:
    #     ontology = requests.get(
    #         ontology_id, params={"apikey": BIOPORTAL_API_KEY}
    #     ).json()["acronym"]
    # except Exception:
    #     ontology = ""
    definition = term.get("definition")
    ontology = ontology_id.split("/")[-1]
    if definition:
        split = definition[0].split()
        if len(split) > 20:
            short = " ".join(split[:20]) + "..."
        else:
            short = definition
        return f"{label}: {short} \t ({ontology})"
    else:
        return f"{label} \t ({ontology})"


@blueprint.route("/new-project/", methods=["GET", "POST"])
@login_required
def new_project():
    form = NewProjectForm()
    # if form.validate_on_submit():
    if request.method == "POST":
        project = Project(
            name=form.name.data,
            comment=form.comment.data,
            user_id=current_user.id,
            group_id=current_user.group_id,
        )
        flash(
            f"New project {project.name} created by user {current_user.id}", "success"
        )
        project.save()
        return redirect(url_for(".new_project"))
    return render_template("annotations/new_project.html", form=form)


@blueprint.route("/")
@login_required
def cards(scope="group"):
    """List cards"""
    if scope == "user":
        user_id = current_user.id
        cards_ = Card.query.filter_by(user_id=user_id)
    elif scope == "group":
        cards_ = Card.query.filter(Card.group_id == current_user.group_id)
    else:
        cards_ = Card.query.all()
    return render_template("annotations/cards.html", cards=cards_)


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
            project_id=form.select_project.data,
            group_id=current_user.group_id,
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
        return redirect(url_for("user.cards"))
    return render_template("annotations/new_card.html", form=form)


@blueprint.route(
    "/delete/<card_id>",
    methods=["GET"],
)
@login_required
def delete_card(card_id):
    card = Card.query.filter_by(id=card_id).first()
    card.delete()
    return redirect(url_for("user.cards"))


@blueprint.route(
    "/edit/<card_id>",
    methods=["GET", "POST"],
)
@login_required
def edit_card(card_id):
    card = Card.query.filter_by(id=card_id).first()
    form = EditCardForm(
        card_id=card_id,
    )

    if form.add_marker.data:
        form.select_markers.append_entry()
        return render_template("annotations/edit_card.html", form=form)
    if form.remove_marker.data and len(form.select_markers):
        form.select_markers.pop_entry()
        return render_template("annotations/edit_card.html", form=form)

    if form.add_gene.data:
        form.select_genes.append_entry()
        return render_template("annotations/edit_card.html", form=form)
    if form.remove_gene.data and len(form.select_genes):
        form.select_genes.pop_entry()
        return render_template("annotations/edit_card.html", form=form)

    # if form.validate_on_submit():
    if request.method == "POST":
        card.update(
            title=form.title.data,
            user_id=current_user.id,
            group_id=current_user.group_id,
            project_id=form.select_project.data,
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
        return redirect(url_for("user.cards"))

    # executed only with a GET
    form.reload_card()

    return render_template("annotations/edit_card.html", form=form)


@blueprint.route(
    "/download/<card_id>",
    methods=["GET"],
)
@login_required
def download_card(card_id):
    card = Card.query.filter_by(id=card_id).first()
    card.update(user_id=current_user.id)
    _, tmp_toml = tempfile.mkstemp(suffix=".toml")
    with open(tmp_toml, "w") as fh:
        fh.write("# omero annotation file\n")
        fh.write(card.as_toml())
        fh.seek(0)
    return send_file(
        tmp_toml,
        as_attachment=True,
        attachment_filename=f'{card.title.replace(" ", "_")}.toml',
    )


@blueprint.route(
    "/clone/<card_id>",
    methods=["GET"],
)
@login_required
def clone_card(card_id):
    card = Card.query.filter_by(id=card_id).first()

    cloned = Card(
        title=_increase_tag(card.title),
        user_id=current_user.id,
        group_id=current_user.group_id,
        project_id=card.project_id,
        organism_id=card.organism_id,
        process_id=card.process_id,
        sample_id=card.sample_id,
        method_id=card.method_id,
        comment=card.comment,
        markers=card.markers,
        genes=card.genes,
    )
    cloned.save()
    flash(f"Card {card.title} cloned by user {current_user.id}", "success")
    return redirect(url_for(f"cards.edit_card", card_id=cloned.id))


@blueprint.route(
    "/print/<card_id>",
    methods=["GET"],
)
@login_required
def print_card(card_id):
    card = Card.query.filter_by(id=card_id).first()
    card_pdf = card.as_pdf()
    return send_file(
        card_pdf,
        as_attachment=True,
        attachment_filename=f'{card.title.replace(" ", "_")}.pdf',
    )


def _increase_tag(title):
    i = 1
    num = title[-i]
    tag = ""
    while num.isdigit():
        tag = num + tag
        i += 1
        num = title[-i]
    if not tag:
        newtitle = title + "1"
    else:
        newtitle = title[: -len(tag)] + str(int(tag) + 1)

    return newtitle
