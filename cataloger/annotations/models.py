# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from cataloger.database import (
    Column,
    PkModel,
    db,
    reference_col,
    relationship,
)

from ..user.models import User


class Card(PkModel):
    """A card is a collection of annotations

    This card can latter be used as key / value annotation tool

    """

    __tablename__ = "cards"
    title = Column(db.String(128), nullable=False)
    user_id = reference_col("users", nullable=True)
    user = relationship("User", backref=__tablename__)
    organism_id = reference_col("organisms", nullable=False)
    organism = relationship("Organism", backref=__tablename__)
    process_id = reference_col("processes", nullable=True)
    process = relationship("Process", backref=__tablename__)
    sample_id = reference_col("samples", nullable=True)
    sample = relationship("Sample", backref=__tablename__)

    def as_csv(self):

        fname = "omero_annotations.csv"
        lines = [
            f"# {self.title}",
            f"# by {self.user.full_name}",
            f"organism,{self.organism.label}",
            f"sample,{self.sample.label}",
            f"process,{self.process.label}",
            "\n",
        ]
        return "\n".join(lines)


class Ontology(PkModel):
    """One of bioportal ontologies
    """

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
    ontology_id = reference_col("ontologies", nullable=True)
    user = relationship("User", backref=__tablename__)
    ontology = relationship("Ontology", backref=__tablename__)


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


class Marker(Annotation):
    """A fluorescent marker or other contrast agent
    """

    __tablename__ = "markers"
    user_id = reference_col("users", nullable=True)
    ontology_id = reference_col("ontologies", nullable=True)
    user = relationship("User", backref=__tablename__)
    ontology = relationship("Ontology", backref=__tablename__)


class Gene(Annotation):
    """An gene (or its corresponding protein)

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


class Method(Annotation):
    """An experimental method

    Examples
    --------
    - optical tweezers
    - laser ablation
    """

    __tablename__ = "methods"
    user_id = reference_col("users", nullable=True)
    ontology_id = reference_col("ontologies", nullable=True)
    user = relationship("User", backref=__tablename__)
    ontology = relationship("Ontology", backref=__tablename__)
