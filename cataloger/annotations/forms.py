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

from cataloger.annotations.models import (
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


class AnnotationForm(FlaskForm):

    select = SelectField("Select the best match", choices=[])
    add = SubmitField("+")
    search = StringField("Search")
    select_new = SelectField("Choose the best match")


class AnnotationFields(FormField):
    @property
    def choices(self):
        log.info("Accessing choices property ")
        return self.select.choices

    @choices.setter
    def choices(self, choices):
        log.info("Setting choices property ")
        self.select.choices = choices

    @property
    def data(self):
        return self.select.data


class NewCardForm(FlaskForm):

    title = StringField("Card title")
    comment = TextAreaField("Comment", widget=TextArea())

    select_project = SelectField("Project")
    select_organism = AnnotationFields(AnnotationForm)
    select_process = AnnotationFields(AnnotationForm)
    select_method = AnnotationFields(AnnotationForm)
    select_sample = AnnotationFields(AnnotationForm)

    select_organism = AnnotationFields(AnnotationForm)
    select_process = AnnotationFields(AnnotationForm)
    select_method = AnnotationFields(AnnotationForm)
    select_sample = AnnotationFields(AnnotationForm)

    select_gene_mods = FieldList(FormField(GeneModForm))
    add_gene_mod = SubmitField("+")
    remove_gene_mod = SubmitField("-")

    save = SubmitField("save")

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

    def create_card(self, current_user):

        gene_mods = [
            get_gene_mod(gm.select_gene.data, gm.select_marker.data)
            for gm in self.select_gene_mods.entries
        ]
        card = Card(
            user_id=current_user.id,
            group_id=current_user.group_id,
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
        return card


class EditCardForm(NewCardForm):
    def __init__(self, card_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.card_id = card_id

    def save_card(self, card_id=None):
        if card_id is None:
            card_id = self.card_id
        card = Card.query.filter_by(id=card_id).first()
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
        log.info("saved card %d", card.id)
        return card.id

    def reload_card(self, card_id=None):
        if card_id is None:
            card_id = self.card_id
        card = Card.query.filter_by(id=card_id).first()

        self.title.data = card.title
        if card.comment:
            self.comment.data = card.comment

        if card.project:
            self.select_project.choices.insert(0, (card.project.id, card.project.name))

        if card.organism:
            self.select_organism.choices.insert(
                0, (card.organism.id, card.organism.label)
            )

        if card.sample:
            self.select_sample.choices.insert(0, (card.sample.id, card.sample.label))

        if card.process:
            self.select_process.choices.insert(0, (card.process.id, card.process.label))

        if card.method:
            self.select_method.choices.insert(0, (card.method.id, card.method.label))

        for gene_mod in card.gene_mods:
            entry = self.select_gene_mods.append_entry()
            entry.select_marker.choices.insert(
                0, (gene_mod.marker_id, gene_mod.marker.label)
            )
            entry.select_gene.choices.insert(0, (gene_mod.gene_id, gene_mod.gene.label))
        return card
