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


class ProjectForm(FlaskForm):
    select = SelectField("Select Project")
    comment = TextAreaField("Comment")
    add = SubmitField("+")
    new = StringField("Name of the new project")


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


class AnnotationForm(FlaskForm):

    select = SelectField("Select the best match", choices=[])
    add = SubmitField("+")
    search = StringField("Search")
    select_new = SelectField("Choose the best match")


class SelectAddFields(FormField):
    @property
    def choices(self):
        log.debug(
            "Accessing choices property for AnnotationField of %s", self.kls.__name__
        )
        return self.select.choices

    @choices.setter
    def choices(self, choices):
        log.debug(
            "Setting choices property  for AnnotationField of %s", self.kls.__name__
        )
        self.select.choices = choices

    @property
    def data(self):
        return self.select.data

    @data.setter
    def data(self, data):
        self.select.data = data


class AnnotationFields(SelectAddFields):
    def __init__(self, kls=None, *args, **kwargs):
        super().__init__(AnnotationForm, *args, **kwargs)
        self.kls = kls


class ProjectFields(SelectAddFields):
    def __init__(self, *args, **kwargs):
        super().__init__(ProjectForm, *args, **kwargs)
        self.kls = Project


class GeneModForm(FlaskForm):
    select_gene = AnnotationFields(Gene)
    select_marker = AnnotationFields(Marker)

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
    comment = TextAreaField("Comment", widget=TextArea())

    select_project = ProjectFields()

    select_organism = AnnotationFields(Organism)
    select_process = AnnotationFields(Process)
    select_method = AnnotationFields(Method)
    select_sample = AnnotationFields(Sample)

    select_gene_mods = FieldList(FormField(GeneModForm))
    add_gene_mod = SubmitField("add gene")
    remove_gene_mod = SubmitField(" remove gene")

    save = SubmitField("save")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._selectors = {
            "organisms": self.select_organism,
            "samples": self.select_sample,
            "processes": self.select_process,
            "methods": self.select_method,
        }

    @property
    def selectors(self):
        for i, entry in enumerate(self.select_gene_mods.entries):
            self._selectors.update(
                {f"gene_{i}": entry.select_gene, f"marker_{i}": entry.select_marker}
            )
        return self._selectors

    def update_choices(self, **filter_by_kwargs):
        self.select_project.choices = [(None, "-")] + [
            (p.id, p.label) for p in Project.query.filter_by(**filter_by_kwargs)
        ]
        for selector in self.selectors.values():
            selector.choices = [(None, "-")] + [
                (instance.id, instance.label)
                for instance in selector.kls.query.filter_by(**filter_by_kwargs)
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
            self.select_project.choices.insert(0, (card.project.id, card.project.label))

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
            if gene_mod.marker:
                entry.select_marker.choices.insert(
                    0, (gene_mod.marker_id, gene_mod.marker.label)
                )
            else:
                entry.select_marker.choices.insert(0, (0, "-"))
            entry.select_gene.choices.insert(0, (gene_mod.gene_id, gene_mod.gene.label))
        return card
