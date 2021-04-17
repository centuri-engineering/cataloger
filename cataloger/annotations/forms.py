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
