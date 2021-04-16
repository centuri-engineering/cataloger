import logging


from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    SubmitField,
    FieldList,
    FormField,
    TextAreaField,
)
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired, Length

from .models import (
    Card,
    Organism,
    Process,
    Sample,
    Marker,
    Gene,
    Method,
    Project,
    get_gene_mod,
)

log = logging.getLogger(__name__)


class SearchAnnotationForm(FlaskForm):
    search_term = StringField("Search for a term")
    submit = SubmitField("?")


class NewAnnotationForm(FlaskForm):
    select_term = SelectField("Select the best match", choices=[])
    submit = SubmitField("ok")


class NewProjectForm(FlaskForm):
    name = StringField("Project name")
    comment = TextAreaField("Comment")
    submit = SubmitField("save")


class MarkerForm(FlaskForm):
    select_marker = SelectField("Marker")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.select_marker.choices = [(p.id, p.label) for p in Marker.query.all()]


class GeneForm(FlaskForm):
    select_gene = SelectField("Gene")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.select_gene.choices = [(p.id, p.label) for p in Gene.query.all()]


class GeneModForm(FlaskForm):
    select_gene = SelectField("Gene")
    select_marker = SelectField("Marker")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.select_marker.choices = [(None, "-")] + [
            (p.id, p.label) for p in Marker.query.all()
        ]
        self.select_gene.choices = [(None, "-")] + [
            (p.id, p.label) for p in Gene.query.all()
        ]


class NewCardForm(FlaskForm):

    title = StringField("Card title")
    select_project = SelectField("Project")
    select_organism = SelectField("Organism")
    select_process = SelectField("Process")
    select_method = SelectField("Method")
    select_sample = SelectField("Sample")

    add_project = SubmitField("+")
    add_organism = SubmitField("+")
    add_process = SubmitField("+")
    add_method = SubmitField("+")
    add_sample = SubmitField("+")

    search_organism = StringField("Search for an organism")
    select_new_organism = SelectField("Select the best match", choices=[])

    select_gene_mods = FieldList(FormField(GeneModForm))
    add_gene_mod = SubmitField("+")
    remove_gene_mod = SubmitField("-")

    comment = TextAreaField("Comment", widget=TextArea())
    submit = SubmitField("save")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.select_project.choices = [(None, "-")] + [
            (p.id, p.name) for p in Project.query.all()
        ]

        self.select_organism.choices = [(None, "-")] + [
            (o.id, o.label) for o in Organism.query.all()
        ]
        self.select_sample.choices = [(None, "-")] + [
            (s.id, s.label) for s in Sample.query.all()
        ]
        self.select_process.choices = [(None, "-")] + [
            (p.id, p.label) for p in Process.query.all()
        ]
        self.select_method.choices = [(None, "-")] + [
            (m.id, m.label) for m in Method.query.all()
        ]


class EditCardForm(NewCardForm):
    def __init__(self, card_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.card_id = card_id

    def save_card(self, card_id=None):
        if card_id is None:
            card_id = self.card_id
        card = self.reload_card(card_id)
        gene_mods = [
            get_gene_mod(gm.select_gene.data, gm.select_marker.data)
            for gm in self.select_gene_mods.entries
        ]

        card.update(
            title=self.title.data,
            project_id=self.select_project.data,
            organism_id=self.select_organism.data,
            process_id=self.select_process.data,
            sample_id=self.select_sample.data,
            method_id=self.select_method.data,
            comment=self.comment.data,
            gene_mods=gene_mods,
        )
        card.save()
        log.info(f"saved card {card.id}")
        return card.id

    def reload_card(self, card_id=None):
        if card_id is None:
            card_id = self.card_id
        card = Card.query.filter_by(id=card_id).first()
        self.title.data = card.title
        if card.comment:
            self.comment.data = card.comment

        if card.project:
            self.select_project.data = card.project.id
            self.select_project.choices = [
                (card.project.id, card.project.name)
            ] + self.select_project.choices

        if card.organism:
            self.select_organism.data = card.organism.id
            self.select_organism.choices = [
                (card.organism.id, card.organism.label),
            ] + self.select_organism.choices

        if card.sample:
            self.select_sample.data = card.sample.id
            self.select_sample.choices = [
                (card.sample.id, card.sample.label),
            ] + self.select_sample.choices

        if card.process:
            self.select_process.data = card.process.id
            self.select_process.choices = [
                (card.process.id, card.process.label),
            ] + self.select_process.choices

        if card.method:
            self.select_method.data = card.method.id
            self.select_method.choices = [
                (card.method.id, card.method.label),
            ] + self.select_method.choices

        for gene_mod in card.gene_mods:
            entry = self.select_gene_mods.append_entry()
            entry.select_marker.data = gene_mod.marker_id
            entry.select_marker.choices = [
                (gene_mod.marker_id, gene_mod.marker.label)
            ] + entry.select_marker.choices

            entry.select_gene.data = gene_mod.gene_id
            entry.select_gene.choices = [
                (gene_mod.gene_id, gene_mod.gene.label)
            ] + entry.select_gene.choices
        return card
