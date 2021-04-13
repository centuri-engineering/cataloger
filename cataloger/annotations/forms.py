from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    SubmitField,
    FieldList,
    FormField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length
from .models import Card, Organism, Process, Sample, Marker, Gene, Method, Project


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


class NewCardForm(FlaskForm):

    title = StringField("Card title")
    select_project = SelectField("Project")
    select_organism = SelectField("Organism")
    select_process = SelectField("Process")
    select_method = SelectField("Method")
    select_sample = SelectField("Sample")

    select_markers = FieldList(FormField(MarkerForm))
    add_marker = SubmitField("+")
    remove_marker = SubmitField("-")

    select_genes = FieldList(FormField(GeneForm))
    add_gene = SubmitField("+")
    remove_gene = SubmitField("-")

    comment = TextAreaField("Comment")

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

    def reload_card(self):

        self.card = Card.query.filter_by(id=self.card_id).first()
        self.title.data = self.card.title

        self.select_project.choices = [
            (self.card.project.id, self.card.project.name)
        ] + self.select_project.choices

        if self.card.organism:
            self.select_organism.choices = [
                (self.card.organism.id, self.card.organism.label),
            ] + self.select_organism.choices
        if self.card.sample:
            self.select_sample.choices = [
                (self.card.sample.id, self.card.sample.label),
            ] + self.select_sample.choices

        if self.card.process:
            self.select_process.choices = [
                (self.card.process.id, self.card.process.label),
            ] + self.select_process.choices

        if self.card.method:
            self.select_method.choices = [
                (self.card.method.id, self.card.method.label),
            ] + self.select_method.choices

        if self.card.comment:
            self.comment.data = self.card.comment

        for marker in self.card.markers:
            self.select_markers.append_entry((marker.id, marker.label))

        for gene in self.card.genes:
            self.select_genes.append_entry((gene.id, gene.label))
