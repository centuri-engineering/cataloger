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
    Tag,
)

log = logging.getLogger(__name__)


class CommentForm(FlaskForm):

    observing = TextAreaField("Observed Process", widget=TextArea())
    conditions = TextAreaField("Experimental Conditions", widget=TextArea())
    additional = TextAreaField("Additional Informations", widget=TextArea())


class CommentFields(FormField):
    def __init__(self, *args, **kwargs):
        super().__init__(CommentForm, *args, **kwargs)

    @property
    def data(self):
        lines = []

        if self.observing.data:
            lines.extend(["Observed Process :", "\n", self.observing.data, "\n"])
        if self.conditions.data:
            lines.extend(["Experimental Conditions :", self.conditions.data, "\n"])
        if self.additional.data:
            lines.extend(["Additional Information :", self.additional.data, "\n"])
        return "\n".join(lines)

    @property
    def tags(self):
        return [w for w in self.data if w.startswith("#")]


class AnnotationForm(FlaskForm):

    select = SelectField(
        "Select the best match",
        render_kw={
            "class": "form-select",
            "style": "text-overflow: ellipsis; width: 100% !important",
        },
        coerce=int,
    )
    add = SubmitField("+", render_kw={"class": "btn btn-light"})
    new = StringField("Enter new term")
    search = StringField("Search")
    select_new = SelectField(
        "Choose the best match",
        render_kw={
            "class": "form-select",
            "style": "text-overflow: ellipsis; width: 100% !important",
        },
    )


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
    def __init__(self, kls=None, free=False, *args, **kwargs):
        super().__init__(AnnotationForm, *args, **kwargs)
        self.kls = kls
        self.free = free


class GeneModForm(FlaskForm):
    select_gene = AnnotationFields(Gene, free=True)
    select_marker = AnnotationFields(Marker, free=True)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.select_marker.choices = [(0, "-")] + [
            (p.id, p.label) for p in Marker.query.all()
        ]
        self.select_gene.choices = [(0, "-")] + [
            (p.id, p.label) for p in Gene.query.all()
        ]


class NewCardForm(FlaskForm):

    title = StringField("Card title")
    comment = CommentFields()

    select_project = AnnotationFields(Project, free=True)
    select_organism = AnnotationFields(Organism)
    select_method = AnnotationFields(Method)
    select_sample = AnnotationFields(Sample)

    select_gene_mods = FieldList(FormField(GeneModForm))
    add_gene_mod = SubmitField("add a channel", render_kw={"class": "btn btn-info"})
    remove_gene_mod = SubmitField(
        "remove last channel", render_kw={"class": "btn btn-secondary"}
    )

    save = SubmitField("save", render_kw={"class": "btn btn-light"})
    cancel = SubmitField("Cancel", render_kw={"class": "btn btn-light"})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._selectors = {
            "project": self.select_project,
            "organisms": self.select_organism,
            "samples": self.select_sample,
            "methods": self.select_method,
        }
        self._tags = (tag.label for tag in Tag.query.all())

    @property
    def tags(self):
        return self._tags

    @property
    def selectors(self):
        for i, entry in enumerate(self.select_gene_mods.entries):
            self._selectors.update(
                {f"gene_{i}": entry.select_gene, f"marker_{i}": entry.select_marker}
            )
        return self._selectors

    def update_choices(self, **filter_by_kwargs):
        self._tags = (tag.label for tag in Tag.query.filter_by(**filter_by_kwargs))

        for selector in self.selectors.values():
            selector.choices = [(0, "-")] + [
                (instance.id, instance.label)
                for instance in selector.kls.query.filter_by(**filter_by_kwargs)
            ]

    def create_card(self, current_user):

        gene_mods = []
        for entry in self.select_gene_mods.entries:

            gm = get_gene_mod(entry.select_gene.data, entry.select_marker.data)
            if gm:
                gene_mods.append(gm)

        gene_mods = [gm for gm in gene_mods if gm]
        title = self.title.data if self.title.data else "Card"
        organism_id = self.select_organism.data if self.select_organism.data else None
        sample_id = self.select_sample.data if self.select_sample.data else None
        method_id = self.select_method.data if self.select_method.data else None

        card = Card(
            user_id=current_user.id,
            group_id=current_user.group_id,
            title=title,
            project_id=self.select_project.data,
            organism_id=organism_id,
            sample_id=sample_id,
            method_id=method_id,
            comment=self.comment.data,
            gene_mods=gene_mods,
        )
        try:
            card.save()
        except Exception as e:
            log.error("Error %s registering card", e)
            return None
        return card


class EditCardForm(NewCardForm):
    def __init__(self, card_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.card_id = card_id

    def save_card(self, card_id=None):
        if card_id is None:
            card_id = self.card_id
        card = Card.query.filter_by(id=card_id).first()
        gene_mods = []
        for entry in self.select_gene_mods.entries:
            gm = get_gene_mod(entry.select_gene.data, entry.select_marker.data)
            if gm and gm.label:
                gene_mods.append(gm)

        organism_id = self.select_organism.data if self.select_organism.data else None
        sample_id = self.select_sample.data if self.select_sample.data else None
        method_id = self.select_method.data if self.select_method.data else None

        card.update(
            title=self.title.data,
            project_id=self.select_project.data,
            organism_id=organism_id,
            sample_id=sample_id,
            method_id=method_id,
            comment=self.comment.data,
            gene_mods=gene_mods,
        )
        card.save()
        log.info("saved card %d", card.id)
        existing_tags = {t.label for t in Tag.query.filter_by(group_id=card.group_id)}
        new_tags = card.tags - existing_tags
        for tag in new_tags:
            Tag(label=tag, group_id=card.group_id).save()
            log.info("saved tag  %s", tag)
        return card.id

    def reload_card(self, card_id=None):
        if card_id is None:
            card_id = self.card_id
        card = Card.query.filter_by(id=card_id).first()

        self.title.data = card.title
        if card.comment:
            observing = []
            conditions = []
            additional = []
            in_observing = False
            in_conditions = False

            for line in card.comment.split("\n"):
                if not line:
                    continue
                if line.startswith("Experimental Conditions"):
                    in_observing = False
                    in_conditions = True
                elif line.startswith("Observed Process"):
                    in_observing = True
                    in_conditions = False
                elif line.startswith("Additional Information"):
                    in_observing = False
                    in_conditions = False
                elif in_observing:
                    observing.append(line)
                elif in_conditions:
                    conditions.append(line)
                else:
                    additional.append(line)

            if observing:
                self.comment.observing.data = "\n".join(observing)
            if conditions:
                self.comment.conditions.data = "\n".join(conditions)
            if additional:
                self.comment.additional.data = "\n".join(additional)

        if card.project:
            self.select_project.choices.insert(0, (card.project.id, card.project.label))

        if card.organism:
            self.select_organism.choices.insert(
                0, (card.organism.id, card.organism.label)
            )

        if card.sample:
            self.select_sample.choices.insert(0, (card.sample.id, card.sample.label))

        if card.process:
            pass

        if card.method:
            self.select_method.choices.insert(0, (card.method.id, card.method.label))

        for gene_mod in card.gene_mods:
            entry = self.select_gene_mods.append_entry()
            if gene_mod.gene_id:
                entry.select_gene.choices.insert(
                    0, (gene_mod.gene_id, gene_mod.gene.label)
                )
            else:
                entry.select_gene.choices.insert(0, (0, "-"))
            if gene_mod.marker_id:
                entry.select_marker.choices.insert(
                    0, (gene_mod.marker_id, gene_mod.marker.label)
                )
            else:
                entry.select_marker.choices.insert(0, (0, "-"))

        return card


class AnnotationLineForm(FlaskForm):
    name = TextAreaField("Category name")
    delete = SubmitField("Delete this term")
    edit = SubmitField("edit")
    see_cards = SubmitField("See associated cards")


class ManageAnnotationForm(FlaskForm):

    annotation_type = SelectField("Annotation type")
    edit_items = FieldList(AnnotationLineForm)
    # list all
    # allow deletion if unused
    # allow edition (?)
    # see related cards

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.annotation_type.choices = [
            (kls, kls.__name__)
            for kls in [Project, Organism, Sample, Marker, Gene, Method, Tag]
        ]
