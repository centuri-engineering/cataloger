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
    current_app,
)

from flask_login import login_required, current_user

from cataloger.annotations.forms import (
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


@blueprint.route("/new-project/", methods=["GET", "POST"])
@login_required
def new_project():
    form = NewProjectForm()
    # if form.validate_on_submit():
    if request.method == "POST":
        project = Project(
            label=form.name.data,
            comment=form.comment.data,
            user_id=current_user.id,
            group_id=current_user.group_id,
        )
        flash(
            f"New project {project.label} created by user {current_user.id}", "success"
        )
        project.save()
        return redirect(url_for(".new_project"))
    return render_template("annotations/new_project.html", form=form)


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


def new_annotation(kls, term, card_id=None):
    """New annotation."""

    match = kls.query.filter_by(label=term["prefLabel"]).first()
    if match:
        flash(f"The term {term['prefLabel']} is already registered", "warning")
        if match.group_id == current_user.group_id:
            return match
        term["@id"] = match.bioportal_id  # use the same ref

    if kls is Organism:
        new = kls(
            label=term["prefLabel"],
            bioportal_id=term["@id"],
            user_id=current_user.id,
            group_id=current_user.group_id,
        )
        new.save()
        flash(f"Term {term['prefLabel']} registered", "success")
        return new

    card = Card.get_by_id(card_id)
    organism_id = card.organism_id if card else 0
    new = kls(
        label=term["prefLabel"],
        bioportal_id=term["@id"],
        organism_id=organism_id,
        user_id=current_user.id,
        group_id=current_user.group_id,
    )
    flash(f"Term {term['prefLabel']} registered", "success")

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


def search_annotation(form, key, selector, card=None):

    search_term = selector.search.data
    flash(f"searching for {search_term}", "info")
    suggestions, choices = annotation_choices(key, search_term=search_term)
    current_app.suggestions = suggestions
    form.update_choices(group_id=current_user.group_id)
    form.reload_card()
    selector.select_new.choices = choices
    if card:
        return render_template(
            "annotations/new_card.html", form=form, new=key, card_id=card.id
        )
    return render_template("annotations/new_card.html", form=form, new=key)


def add_annotation(form, key, selector, card=None):

    term = current_app.suggestions[selector.select_new.data]
    new = new_annotation(selector.kls, term)

    selector.choices.insert(0, (new.id, new.label))
    selector.data = new.id
    if card:
        card.update(organism_id=new.id)
        return redirect(url_for("cards.edit_card", card_id=form.card_id))
    return render_template("annotations/new_card.html", form=form)


@blueprint.route(
    "/edit/<card_id>",
    methods=["GET", "POST"],
    defaults={"card_id": 0, "new": "none", "search": "none"},
)
@blueprint.route(
    "/edit/<card_id>",
    methods=["GET", "POST"],
)
@login_required
def edit_card(card_id, search=None, new=None):

    card = Card.query.filter_by(id=card_id).first()
    if card.user_id != current_user.id:
        flash("You can only edit your own cards, consider cloning instead")
        return redirect(url_for("user.cards"))
    form = EditCardForm(card_id=card_id)
    form.update_choices(group_id=current_user.group_id)
    for key, selector in form.selectors.items():
        if selector.search.data:
            search = key
            return search_annotation(form, search, selector, card)
        if selector.select_new.data:
            return add_annotation(form, key, selector, card)

    if form.add_gene_mod.data:
        form.select_gene_mods.append_entry()
        return render_template("annotations/edit_card.html", form=form, card_id=card_id)

    if form.remove_gene_mod.data and len(form.select_gene_mods):
        form.select_gene_mods.pop_entry()
        return render_template("annotations/edit_card.html", form=form, card_id=card_id)
    for key, selector in form.selectors.items():
        if selector.add.data:
            flash(f"now searching for new {key}", "warning")
            return render_template(
                "annotations/edit_card.html", form=form, search=key, card_id=card_id
            )
    if request.method == "POST":  # form.validate_on_submit():
        flash(f"Edited {card.title} by user {current_user.username}", "success")
        form.save_card()
        return redirect(url_for("user.cards"))
    form.reload_card()
    return render_template(
        "annotations/edit_card.html", form=form, search=search, new=new, card_id=card_id
    )


@blueprint.route(
    "/new-card/",
    methods=["GET", "POST"],
)
@login_required
def new_card():
    """Creates a card"""

    form = NewCardForm()
    form.update_choices(group_id=current_user.group_id)

    for key, selector in form.selectors.items():
        if selector.search.data:
            search = key
            return search_annotation(form, search, selector, card=None)
        if selector.select_new.data:
            return add_annotation(form, key, selector, card=None)

    if form.add_gene_mod.data:
        form.select_gene_mods.append_entry()
        return render_template("annotations/new_card.html", form=form)

    if form.remove_gene_mod.data and len(form.select_gene_mods):
        form.select_gene_mods.pop_entry()
        return render_template("annotations/new_card.html", form=form)

    if request.method == "POST":  #  form.validate_on_submit():
        card = form.create_card(current_user)
        return redirect(url_for("user.cards", card_id=card.id))

    for key, selector in form.selectors.items():
        if selector.add.data:
            flash(f"now searching for new {key}", "warning")
            return render_template("annotations/new_card.html", form=form, search=key)

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
    return redirect(
        url_for(
            f"cards.edit_card",
            card_id=cloned.id,
        )
    )


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
