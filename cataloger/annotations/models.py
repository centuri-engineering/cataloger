# -*- coding: utf-8 -*-
"""User models."""
import os
import tempfile
import subprocess
import datetime as dt
import toml

from sqlalchemy.exc import OperationalError


from cataloger.database import (
    Column,
    PkModel,
    db,
    reference_col,
    relationship,
)

from ..user.models import User

"""Many to many tables
"""

marker_card = db.Table(
    "marker_card",
    db.Model.metadata,
    Column("marker_id", db.Integer, db.ForeignKey("markers.id")),
    Column("card_id", db.Integer, db.ForeignKey("cards.id")),
)

gene_card = db.Table(
    "gene_card",
    db.Model.metadata,
    Column("gene_id", db.Integer, db.ForeignKey("genes.id")),
    Column("card_id", db.Integer, db.ForeignKey("cards.id")),
)


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
    process_id = reference_col("processes", nullable=True)
    process = relationship("Process", backref=__tablename__)
    sample_id = reference_col("samples", nullable=True)
    sample = relationship("Sample", backref=__tablename__)
    method_id = reference_col("methods", nullable=True)
    method = relationship("Method", backref=__tablename__)
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    markers = relationship("Marker", secondary=marker_card)
    genes = relationship("Gene", secondary=gene_card)
    comment = Column(db.String, nullable=True)

    def as_csv(self):
        """Writes the key - value pairs of the cards as CSV"""
        username = self.user.full_name if self.user.first_name else self.user.username
        lines = [
            f"# {self.title}",
            f"# {self.created_at}",
            f"# by {username}",
            f"# for project {self.project.name}",
            "# ",
            f"# {self.comment}",
            f"organism,{self.organism.label}",
            f"sample,{self.sample.label}",
            f"method,{self.method.label}",
            f"process,{self.process.label}",
        ]
        lines += [f"marker_{i},{m.label}" for i, m in enumerate(self.markers)]
        try:
            lines += [f"gene_{i},{g.label}" for i, g in enumerate(self.genes)]
        except OperationalError:  # TODO why?
            pass
        return "\n".join(lines)

    def as_dict(self):

        kv_pairs = {}
        if self.organism:
            kv_pairs["organism"] = self.organism.label
        if self.sample:
            kv_pairs["sample"] = self.sample.label
        if self.process:
            kv_pairs["process"] = self.process.label
        if self.method:
            kv_pairs["method"] = self.method.label

        kv_pairs.update({f"marker_{i}": m.label for i, m in enumerate(self.markers)})
        kv_pairs.update({f"gene_{i}": g.label for i, g in enumerate(self.genes)})
        tags = [w for w in self.comment.split() if w.startswith("#")]
        card_dict = {
            "title": self.title,
            "created": self.created_at,
            "project": self.project.name,
            "user": self.user.username,
            "comment": self.comment,
            "kv_pairs": kv_pairs,
            "tags": tags,
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


class Project(PkModel):
    __tablename__ = "projects"
    name = Column(db.String(128), nullable=False)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    user_id = reference_col("users", nullable=False)
    user = relationship("User", backref=__tablename__)
    group_id = reference_col("groups", nullable=False)
    group = relationship("Group", backref=__tablename__)
    comment = Column(db.String, nullable=True)


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


class Organism(Annotation):
    """An organism in the taxonomy sense,


    Examples
    --------
    - fruit fly (Drosophila melanogaster)
    - mouse (Mus musculus)
    - human (Homo sapiens)
    """

    __tablename__ = "organisms"
    user_id = reference_col("users", nullable=True)
    ontology_id = reference_col("ontologies", nullable=True)
    user = relationship("User", backref=__tablename__)
    ontology = relationship("Ontology", backref=__tablename__)


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
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref=__tablename__)
    ontology_id = reference_col("ontologies", nullable=True)
    ontology = relationship("Ontology", backref=__tablename__)
    organism_id = reference_col("organisms", nullable=False)
    organism = relationship("Organism", backref=__tablename__)


class Sample(Annotation):
    """The biological sample studied

    Examples
    --------
    - a cell line (e.g. HCT116)
    - an organ (e.g. cerebelum)
    - a tissue (e.g. the drosophila wing disk)
    - an organelle
    """

    __tablename__ = "samples"
    user_id = reference_col("users", nullable=True)
    ontology_id = reference_col("ontologies", nullable=True)
    user = relationship("User", backref=__tablename__)
    ontology = relationship("Ontology", backref=__tablename__)
    organism_id = reference_col("organisms", nullable=False)
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
    user_id = reference_col("users", nullable=True)
    ontology_id = reference_col("ontologies", nullable=True)
    user = relationship("User", backref=__tablename__)
    ontology = relationship("Ontology", backref=__tablename__)


class Marker(Annotation):
    """A fluorescent marker or other contrast agent"""

    __tablename__ = "markers"
    user_id = reference_col("users", nullable=True)
    ontology_id = reference_col("ontologies", nullable=True)
    user = relationship("User", backref=__tablename__)
    ontology = relationship("Ontology", backref=__tablename__)
    organism_id = reference_col("organisms", nullable=False)
    organism = relationship("Organism", backref=__tablename__)


class Gene(Annotation):
    """A gene (or its corresponding protein)

    Examples
    --------
    - alpha-tubulin
    - Myosin II
    - CDC52
    """

    __tablename__ = "genes"
    user_id = reference_col("users", nullable=True)
    ontology_id = reference_col("ontologies", nullable=True)
    user = relationship("User", backref=__tablename__)
    ontology = relationship("Ontology", backref=__tablename__)
    organism_id = reference_col("organisms", nullable=False)
    organism = relationship("Organism", backref=__tablename__)
