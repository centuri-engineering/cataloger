# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt
import toml
import logging


from cataloger.database import (
    Column,
    PkModel,
    db,
    reference_col,
    relationship,
)

log = logging.getLogger(__name__)

"""Many to many tables
"""

gene_mod_card = db.Table(
    "gene_mode_card",
    db.Model.metadata,
    Column("gene_mod_id", db.Integer, db.ForeignKey("gene_mods.id")),
    Column("card_id", db.Integer, db.ForeignKey("cards.id")),
)


class Tag(PkModel):
    """A single word tag"""

    __tablename__ = "tags"
    label = Column(db.String(128), nullable=False)
    group_id = reference_col("groups", nullable=True)
    group = relationship("Group", backref=__tablename__)


class Card(PkModel):
    """A card is a collection of annotations

    This card can latter be used as key / value annotation tool

    """

    __tablename__ = "cards"
    title = Column(db.String(128), nullable=False)
    user_id = reference_col("users", nullable=False)
    user = relationship("User", backref=__tablename__)
    group_id = reference_col("groups", nullable=True)
    group = relationship("Group", backref=__tablename__)
    project_id = reference_col("projects", nullable=True)
    project = relationship("Project", backref=__tablename__)
    organism_id = reference_col("organisms", nullable=False)
    organism = relationship("Organism", backref=__tablename__)
    sample_id = reference_col("samples", nullable=True)
    sample = relationship("Sample", backref=__tablename__)
    process_id = reference_col("processes", nullable=True)
    process = relationship("Process", backref=__tablename__)
    method_id = reference_col("methods", nullable=True)
    method = relationship("Method", backref=__tablename__)
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    gene_mods = relationship("GeneMod", secondary=gene_mod_card)
    comment = Column(db.String, nullable=True)

    def as_csv(self):
        """Writes the key - value pairs of the cards as CSV"""
        username = self.user.full_name if self.user.first_name else self.user.username
        lines = [
            f"# {self.title}",
            f"# {self.created_at}",
            f"# by {username}",
            f"# for project {self.project.label}",
            "# ",
            f"# {self.comment}",
            f"organism,{self.organism.label}",
            f"sample,{self.sample.label}",
            f"method,{self.method.label}",
        ]
        lines += [f"channel_{i},{gm.label}" for i, gm in enumerate(self.gene_mods)]
        return "\n".join(lines)

    @property
    def tags(self):
        _tags = [w.lstrip("#") for w in self.comment.split() if w.startswith("#")]
        return set(_tags)

    def as_dict(self):

        kv_pairs = {}
        if self.organism:
            kv_pairs["organism"] = self.organism.label
        if self.sample:
            kv_pairs["sample"] = self.sample.label
        if self.method:
            kv_pairs["method"] = self.method.label
        if self.process:
            kv_pairs["process"] = self.method.label

        kv_pairs.update(
            {f"channel_{i}": gm.label for i, gm in enumerate(self.gene_mods)}
        )

        card_dict = {
            "title": self.title,
            "created": self.created_at,
            "project": self.project.label,
            "user": self.user.username,
            "group": self.group.groupname,
            "comment": self.comment,
            "kv_pairs": kv_pairs,
            "tags": self.tags,
            "accessed": str(dt.datetime.utcnow()),
        }
        return card_dict

    def as_toml(self):
        """Output the card contents as toml"""
        return toml.dumps(self.as_dict())

    def as_markdown(self):
        """Writes the card contents as markdown"""
        as_dict = self.as_dict()
        lines = [
            f"# {self.title}\n\n",
            f"Created by {self.user.username}\n",
            self.comment.replace("#", ""),
            "## Key-value pairs:",
            "|-----|------|",
        ]
        for k, v in as_dict["kv_pairs"].items():
            lines.append(f"| {k} | {v} |")
        lines.append("|-----|------|\n")
        lines.append("## Tags:")
        lines.append(" ".join([f"**{tag}**" for tag in as_dict["tags"]]))

        return "\n".join(lines)

    @property
    def html_comment(self):

        lines = []
        for line in self.comment.split("\n"):
            if (
                line.startswith("Observed Process")
                or line.startswith("Experimental Conditions")
                or line.startswith("Additional Information")
            ):
                lines.append(f"""<h5 style="margin-top: 1rem;"> {line} </h5>""")
            else:
                line = " ".join(
                    [f"<b>{w}</b>" if w.startswith("#") else w for w in line.split(" ")]
                )
                lines.append(line)

        html = "\n".join(lines)
        return html


class Ontology(PkModel):
    """One of bioportal ontologies"""

    __tablename__ = "ontologies"
    acronym = Column(db.String(30), nullable=False)
    name = Column(db.String(128), nullable=False)
    bioportal_id = Column(db.String(128), nullable=False)


class Annotation(PkModel):
    """An abstract annotation class

    An annotation corresponds to an entity from one of
    bioportal ontologies.

    """

    __abstract__ = True
    label = Column(db.String(128), nullable=False)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    bioportal_id = Column(db.String(128), nullable=True)
    __icon__ = "fa-search"
    __label__ = "Abstract annotation"

    @classmethod
    def help(cls):
        return cls.__doc__.split("\n")[0]


class Project(Annotation):
    """The project associtated with this experiment"""

    __tablename__ = "projects"
    user_id = reference_col("users", nullable=False)
    user = relationship("User", backref=__tablename__)
    group_id = reference_col("groups", nullable=False)
    group = relationship("Group", backref=__tablename__)
    organism_id = reference_col("organisms", nullable=True)
    organism = relationship("Organism", backref=__tablename__)
    __icon__ = "fa-search"
    __label__ = "Project"


class Organism(Annotation):
    """An organism in the taxonomy sense


    Examples
    --------
    - fruit fly (Drosophila melanogaster)
    - mouse (Mus musculus)
    - Xaenopus Laevis egg extract
    """

    __tablename__ = "organisms"
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref=__tablename__)
    ontology_id = reference_col("ontologies", nullable=True)
    ontology = relationship("Ontology", backref=__tablename__)
    group_id = reference_col("groups", nullable=True)
    group = relationship("Group", backref=__tablename__)

    __icon__ = "fa-bug"
    __label__ = "Organism"


class Process(Annotation):
    """The biological process being studied

    Examples
    --------
    - mesoderm invagination
    - epithelio-mesenchymal transition
    - colon cancer
    - senescence
    """

    __tablename__ = "processes"
    __icon__ = "fa-cogs"
    __label__ = "Observed Process"
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref=__tablename__)
    group_id = reference_col("groups", nullable=True)
    group = relationship("Group", backref=__tablename__)
    ontology_id = reference_col("ontologies", nullable=True)
    ontology = relationship("Ontology", backref=__tablename__)
    organism_id = reference_col("organisms", nullable=True)
    organism = relationship("Organism", backref=__tablename__)


class Sample(Annotation):
    """The biological sample studied

    Examples
    --------
    - a cell population within the model (e.g. the mesoderm)
    - an organ (e.g. cerebelum)
    - a part of the epithelium (e.g apical)
    - an organelle
    """

    __tablename__ = "samples"
    __icon__ = "fa-flask"
    __label__ = "Sample"
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref=__tablename__)
    group_id = reference_col("groups", nullable=True)
    group = relationship("Group", backref=__tablename__)
    ontology_id = reference_col("ontologies", nullable=True)
    ontology = relationship("Ontology", backref=__tablename__)
    organism_id = reference_col("organisms", nullable=True)
    organism = relationship("Organism", backref=__tablename__)


class Method(Annotation):
    """An experimental method

    Examples
    --------
    - optical tweezers
    - laser ablation
    - FISH
    """

    __tablename__ = "methods"
    __icon__ = "fa-tools"
    __label__ = "Method"
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref=__tablename__)
    group_id = reference_col("groups", nullable=True)
    group = relationship("Group", backref=__tablename__)
    ontology_id = reference_col("ontologies", nullable=True)
    ontology = relationship("Ontology", backref=__tablename__)
    organism_id = reference_col("organisms", nullable=True)
    organism = relationship("Organism", backref=__tablename__)


class Marker(Annotation):
    """A fluorescent marker, other contrast agent, or gene modification

    Examples
    --------
    - eGFP
    - Alexa 488
    - RNAi
    """

    __tablename__ = "markers"
    __icon__ = "fa-map-marker"
    __label__ = "Marker"
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref=__tablename__)
    group_id = reference_col("groups", nullable=True)
    group = relationship("Group", backref=__tablename__)
    ontology_id = reference_col("ontologies", nullable=True)
    ontology = relationship("Ontology", backref=__tablename__)
    organism_id = reference_col("organisms", nullable=True)
    organism = relationship("Organism", backref=__tablename__)


class Gene(Annotation):
    """A target protein, primary antibody or other biochemical element

    Examples
    --------
    - alpha-tubulin
    - Myosin II
    - CDC52
    """

    __tablename__ = "genes"
    __icon__ = "fa-bullseye"
    __label__ = "Target"
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref=__tablename__)
    ontology_id = reference_col("ontologies", nullable=True)
    group_id = reference_col("groups", nullable=True)
    group = relationship("Group", backref=__tablename__)
    ontology = relationship("Ontology", backref=__tablename__)
    organism_id = reference_col("organisms", nullable=True)
    organism = relationship("Organism", backref=__tablename__)


class GeneMod(Annotation):
    """A protein / target pair

    Examples
    --------
    - alpha-tubulin GFP
    - P53-Alexa488
    """

    __tablename__ = "gene_mods"
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref=__tablename__)
    group_id = reference_col("groups", nullable=True)
    group = relationship("Group", backref=__tablename__)
    gene_id = reference_col("genes", nullable=True)
    gene = relationship("Gene", backref=__tablename__)
    marker_id = reference_col("markers", nullable=True)
    marker = relationship("Marker", backref=__tablename__)


def get_gene_mod(gene_id, marker_id):
    """Retrieves a GeneMod model if the gene / marker pair already exists,
    or creates a new one
    """

    if gene_id in ("None", None):
        gene_id = 0

    if marker_id in ("None", None):
        marker_id = 0

    gene_mod = GeneMod.query.filter_by(gene_id=gene_id, marker_id=marker_id).first()
    if gene_mod:
        log.info("Found gene_mod for gene %s and marker %s", gene_id, marker_id)
        return gene_mod

    gene = Gene.get_by_id(gene_id)
    marker = Marker.get_by_id(marker_id)
    if not (gene or marker):
        return None

    gene_label = gene.label if gene else ""
    gene_id = gene.bioportal_id if gene else ""
    marker_label = marker.label if marker else ""
    marker_id = marker.bioportal_id if marker else ""
    user_id = gene.user_id if gene else marker.user_id
    group_id = gene.group_id if gene else marker.group_id

    label = f"{gene_label}-{marker_label}"
    bioportal_id = f"{gene_id}-{marker_id}"
    gene_mod = GeneMod(
        label=label,
        bioportal_id=bioportal_id,
        user_id=user_id,
        group_id=group_id,
    )
    if gene:
        gene_mod.update(gene=gene, gene_id=gene_id, commit=False)
    if marker:
        gene_mod.update(marker=marker, marker_id=marker_id, commit=False)

    gene_mod.save()
    return gene_mod
