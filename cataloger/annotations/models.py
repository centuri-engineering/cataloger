# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from flask_login import UserMixin

from cataloger.database import (
    Column,
    PkModel,
    db,
    reference_col,
    relationship,
)


def make_relation(left, right="ontologies"):

    return db.Table(
        f"{left}_{right}",
        db.Base.metadata,
        Column(left, db.ForeignKey(f"{left}.id")),
        Column(right, db.ForeignKey(f"{right}.id")),
    )


class Ontologies(PkModel):

    __tablename__ = "ontologies"
    acronym = Column(db.String(30), nullable=False)
    name = Column(db.String(128), nullable=False)
    bioportal_id = Column(db.String(128), nullable=False)


class Annotation(PkModel):

    __abstract__ = True
    label = Column(db.String(128), nullable=False)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    bioportal_id = Column(db.String(128), nullable=True)


class Organisms(Annotation):
    __tablename__ = "organisms"
    ontologies = relationship("Ontologies", secondary=make_relation("organisms"))


class Processes(Annotation):
    __tablename__ = "processes"
    ontologies = relationship("Ontologies", secondary=make_relation("processes"))


class Genes(Annotation):
    __tablename__ = "genes"
    ontologies = relationship("Ontologies", secondary=make_relation("genes"))


class Proteins(Annotation):
    __tablename__ = "proteins"
    ontologies = relationship("Ontologies", secondary=make_relation("proteins"))


class Fluorophores(Annotation):
    __tablename__ = "fluorophores"
    ontologies = relationship("Ontologies", secondary=make_relation("fluorophores"))
