# -*- coding: utf-8 -*-
"""annotation views."""
import os
import requests
import tempfile
import logging
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
    current_app,
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
    GeneMod,
    get_gene_mod,
)


from cataloger.utils import get_url_prefix

log = logging.getLogger(__name__)

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


def annotation_choices(cls, search_term=None):
    if search_term is None:
        search_term = request.args.get("search_term")
    suggestions = search_bioportal(search_term)  # , ontologies=ontologies[cls])

    if not suggestions:
        flash(
            """Sorry, no results found. Please reformulate your query,
 maybe with more general terms, and check for typos""",
            "warning",
        )

    uniq = {_format_label(term): term_id for term_id, term in suggestions.items()}
    choices = [(v, k) for k, v in uniq.items()]
    return suggestions, choices


def new_annotation(cls, term, card_id=None):
    """New annotation."""

    match = classes[cls].query.filter_by(label=term["prefLabel"]).first()
    if match:
        flash(f"The term {term['prefLabel']} is already registered", "warning")
        return match

    if cls in ("organisms", "methods"):
        new = classes[cls](label=term["prefLabel"], bioportal_id=term["@id"])
        return new

    card = Card.get_by_id(card_id)
    organism_id = card.organism_id if card else 0
    new = classes[cls](
        label=term["prefLabel"],
        bioportal_id=term["@id"],
        organism_id=organism_id,
    )
    flash(f"Term {term['prefLabel']}registered", "success")

    new.save()
    return new


def _format_label(term):
    label = term["prefLabel"]
    ontology_id = term["links"]["ontology"]
    definition = term.get("definition")
    ontology = ontology_id.split("/")[-1]
    if definition:
        split = definition[0].split()
        if len(split) > 8:
            short = " ".join(split[:8]).split(".")[0] + "..."
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
    if form.title.data:
        card = Card(
            title=form.title.data,
            user_id=current_user.id,
            group_id=current_user.group_id,
            organism_id=0,
        )
        card.save()
        form.card_id = card.id
        return redirect(url_for("cards.edit_card", card_id=card.id))

    return render_template("annotations/new_card.html", form=form)


@blueprint.route(
    "/delete/<card_id>",
    methods=["GET"],
)
@login_required
def delete_card(card_id):
    card = Card.query.filter_by(id=card_id).first()
    if not card.user_id == current_user.id:
        flash("You can only delete your own cards")
        return redirect(url_for("user.cards"))

    card.delete()

    return redirect(url_for("user.cards"))


@blueprint.route(
    "/edit/<card_id>",
    methods=["GET", "POST"],
)
@login_required
def edit_card(card_id):
    card = Card.query.filter_by(id=card_id).first()

    if not card.user_id == current_user.id:
        flash("You can only edit your own cards, consider cloning instead")
        return redirect(url_for("user.cards"))
    form = EditCardForm(card_id=card_id)

    if form.add_organism.data and form.search_organism.data:
        flash("searching for new organisms")
        search_term = form.search_organism.data
        suggestions, choices = annotation_choices("organisms", search_term=search_term)
        current_app.suggestions = suggestions
        form.select_new_organism.choices = choices
        return render_template("annotations/edit_card.html", form=form, new="organisms")
    if form.select_new_organism.data:
        term = current_app.suggestions[form.select_new_organism.data]
        new = new_annotation("organisms", term)
        form.select_organism.choices.insert(0, (new.id, new.label))
        form.select_organism.data = new.id
        return render_template("annotations/edit_card.html", form=form)

    if form.add_gene_mod.data:
        form.select_gene_mods.append_entry()
        return render_template("annotations/edit_card.html", form=form)

    if form.remove_gene_mod.data and len(form.select_gene_mods):
        form.select_gene_mods.pop_entry()
        return render_template("annotations/edit_card.html", form=form)

    if form.submit.data:
        flash(f"New Form title: {form.title.data}", "warning")
        flash(f"Edited {card.title} by user {current_user.id}", "success")
        save_card(form)
        return redirect(url_for("cards.edit_card", card_id=card.id))

    # executed only with a GET
    reload_card(form)
    flash(f"Old Form title: {form.title.data}", "warning")

    return render_template("annotations/edit_card.html", form=form)


def save_card(form, card_id=None):
    if card_id is None:
        card_id = form.card_id
    card = Card.query.filter_by(id=card_id).first()
    gene_mods = [
        get_gene_mod(gm.select_gene.data, gm.select_marker.data)
        for gm in form.select_gene_mods.entries
    ]

    card.update(
        title=form.title.data,
        project_id=form.select_project.data,
        organism_id=form.select_organism.data,
        process_id=form.select_process.data,
        sample_id=form.select_sample.data,
        method_id=form.select_method.data,
        comment=form.comment.data,
        gene_mods=gene_mods,
    )
    card.save()
    log.info("saved card %d", card.id)
    return card.id


def reload_card(form, card_id=None):
    if card_id is None:
        card_id = form.card_id
    card = Card.query.filter_by(id=card_id).first()
    form.title.data = card.title
    if card.comment:
        form.comment.data = card.comment

    if card.project:
        form.select_project.data = card.project.id
        form.select_project.choices.insert(0, (card.project.id, card.project.name))

    if card.organism:
        form.select_organism.data = card.organism.id
        form.select_organism.choices.insert(0, (card.organism.id, card.organism.label))

    if card.sample:
        form.select_sample.data = card.sample.id
        form.select_sample.choices.insert(0, (card.sample.id, card.sample.label))

    if card.process:
        form.select_process.data = card.process.id
        form.select_process.choices.insert(0, (card.process.id, card.process.label))

    if card.method:
        form.select_method.data = card.method.id
        form.select_method.choices.insert(0, (card.method.id, card.method.label))

    for gene_mod in card.gene_mods:
        entry = form.select_gene_mods.append_entry()
        entry.select_marker.data = gene_mod.marker_id
        entry.select_marker.choices.insert(
            0, (gene_mod.marker_id, gene_mod.marker.label)
        )

        entry.select_gene.data = gene_mod.gene_id
        entry.select_gene.choices.insert(0, (gene_mod.gene_id, gene_mod.gene.label))
    return card


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
