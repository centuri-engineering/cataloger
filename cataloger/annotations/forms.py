from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, FieldList, FormField
from wtforms.validators import DataRequired, Length
from .models import Organism, Process, Sample, Marker, Gene, Method


class SearchAnnotationForm(FlaskForm):
    search_term = StringField("Search for a term")
    submit = SubmitField("?")


class NewAnnotationForm(FlaskForm):
    select_term = SelectField("Select the best match", choices=[])
    submit = SubmitField("ok")


class MarkerForm(FlaskForm):
    select_marker = SelectField("Marker")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.select_marker.choices = [(p.id, p.label) for p in Marker.query.all()]


class NewCardForm(FlaskForm):

    title = StringField("Card title")
    select_organism = SelectField("Organism")
    select_process = SelectField("Process")
    select_sample = SelectField("Sample")
    select_markers = FieldList(FormField(MarkerForm))
    add_marker = SubmitField("+")

    submit = SubmitField("ok")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.select_organism.choices = [(o.id, o.label) for o in Organism.query.all()]
        self.select_sample.choices = [(s.id, s.label) for s in Sample.query.all()]
        self.select_process.choices = [(p.id, p.label) for p in Process.query.all()]
